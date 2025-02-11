# scripts/main.py

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import re

# Import our existing modules
from scripts.prompts import (
    create_clinical_prompt, 
    create_disease_prompt, 
    create_pharma_prompt, 
    get_llm_response
)
from scripts.models import hybrid_search, build_index
from scripts.clinical import load_clinical_documents
from scripts.disease import load_disease_documents
from scripts.pharma import load_pharma_documents, load_pharma_structured_documents, format_pharma

app = FastAPI(title="VetLLM REST API")

# -------------------------
# Load Data and Build Indexes
# -------------------------
clinical_docs = load_clinical_documents()
disease_docs = load_disease_documents()
pharma_docs = load_pharma_documents()
raw_pharma_docs = load_pharma_structured_documents()

index_clinical, _ = build_index(clinical_docs, "database/embeddings_clinical.npy")
index_disease, _ = build_index(disease_docs, "database/embeddings_disease.npy")
index_pharma, _ = build_index(pharma_docs, "database/embeddings_pharma.npy")

# Group document collections by category.
doc_collections = {
    "clinical": (clinical_docs, index_clinical),
    "disease": (disease_docs, index_disease),
    "pharma": (pharma_docs, index_pharma)
}

# -------------------------
# Request Model
# -------------------------
class QueryRequest(BaseModel):
    query: str
    endpoint: str  # e.g., "synonym", "diagnostic_workup", etc.
    provider: str  # "Ollama" or "Gemini"

# -------------------------
# Helper Function for Pharma Dose Rate Calculation
# -------------------------
def process_pharma_dose_rate(ingredient_query: str, weight: float, animal: str, raw_pharma_docs) -> (str, str):
    """
    Iterates through structured pharma documents to find an exact (or near‑exact)
    match on the Active Ingredient, Ingredient, or Trade Name.
    If a match is found, looks up the dose rate for the given animal type,
    calculates the dose, and returns a response with a reference.
    """
    for doc in raw_pharma_docs:
        active_ing = doc.get("Active Ingredient", "").lower().strip()
        ing = doc.get("Ingredient", "").lower().strip()
        trade_name = doc.get("Trade Name", "").lower().strip()
        query_tokens = ingredient_query.lower().split()
        # If single token, compare it to the first token of each field.
        if len(query_tokens) == 1:
            if (active_ing.split()[0] == query_tokens[0] or
                ing.split()[0] == query_tokens[0] or
                trade_name.split()[0] == query_tokens[0]):
                dose_rate_info = doc.get("pharma_info", {}).get("dose_rate", {})
                dose_rate_str = dose_rate_info.get(animal, None)
                if dose_rate_str is None:
                    return (f"No dose rate information available for {animal}.",
                            f"Candidate:\n{format_pharma(doc)}")
                num_match = re.search(r"([\d\.]+)", dose_rate_str)
                if not num_match:
                    return (f"Could not parse dose rate value for {animal}.",
                            f"Candidate:\n{format_pharma(doc)}")
                rate = float(num_match.group(1))
                calculated_dose = rate * weight
                response = (f"Calculated dose for '{doc.get('Active Ingredient')}' in a {weight} kg {animal}: "
                            f"{calculated_dose} mg (@{rate} mg/kg).")
                reference = f"Candidate (Exact Match):\n{format_pharma(doc)}"
                return response, reference
        else:
            # For multi-word queries, use substring matching.
            if (ingredient_query.lower() in active_ing or 
                ingredient_query.lower() in ing or 
                ingredient_query.lower() in trade_name):
                dose_rate_info = doc.get("pharma_info", {}).get("dose_rate", {})
                dose_rate_str = dose_rate_info.get(animal, None)
                if dose_rate_str is None:
                    return (f"No dose rate information available for {animal}.",
                            f"Candidate:\n{format_pharma(doc)}")
                num_match = re.search(r"([\d\.]+)", dose_rate_str)
                if not num_match:
                    return (f"Could not parse dose rate value for {animal}.",
                            f"Candidate:\n{format_pharma(doc)}")
                rate = float(num_match.group(1))
                calculated_dose = rate * weight
                response = (f"Calculated dose for '{doc.get('Active Ingredient')}' in a {weight} kg {animal}: "
                            f"{calculated_dose} mg (@{rate} mg/kg).")
                reference = f"Candidate (Exact Match):\n{format_pharma(doc)}"
                return response, reference
    return ("No exact match found for the specified ingredient.", "")

# -------------------------
# API Endpoints
# -------------------------

# Clinical Data Endpoint
@app.post("/clinical/{sub_endpoint}")
def process_clinical(sub_endpoint: str, request: QueryRequest):
    """
    Processes a clinical query.
    sub_endpoint can be one of: "synonym", "diagnostic_workup", "drug_of_choice", 
    "differential_diagnosis", "line_of_treatment", "prognosis".
    """
    candidates = hybrid_search(request.query, {"clinical": doc_collections["clinical"]})
    if candidates:
        best_doc = candidates[0]
        full_text = best_doc["text"]
        prompt = create_clinical_prompt(request.query, full_text, sub_endpoint)
        response = get_llm_response(prompt, request.provider)
        reference = "\n\n".join([f"Match {i+1}:\n{cand['text']}" for i, cand in enumerate(candidates)])
    else:
        response = "No relevant clinical data found."
        reference = ""
    return {"response": response, "reference": reference}

# Disease Symptoms Endpoint
@app.post("/disease/{sub_endpoint}")
def process_disease(sub_endpoint: str, request: QueryRequest):
    """
    Processes a disease symptoms query.
    sub_endpoint can be one of: "describe_clinical_signs", "symptoms", "reverse_symptom_lookup".
    """
    candidates = hybrid_search(request.query, {"disease": doc_collections["disease"]})
    if candidates:
        best_doc = candidates[0]
        full_text = best_doc["text"]
        prompt = create_disease_prompt(request.query, full_text, sub_endpoint)
        response = get_llm_response(prompt, request.provider)
        reference = "\n\n".join([f"Match {i+1}:\n{cand['text']}" for i, cand in enumerate(candidates)])
    else:
        response = "No relevant disease data found."
        reference = ""
    return {"response": response, "reference": reference}

# Pharma Endpoint
@app.post("/pharma/{sub_endpoint}")
def process_pharma(sub_endpoint: str, request: QueryRequest):
    """
    Processes a pharmaceutical query.
    sub_endpoint can be one of: "calculate_dose_rate", "indication", "contraindication",
    "mechanism_of_action", "metabolism_and_elimination", "products".
    
    If the sub_endpoint is "calculate_dose_rate", the query is parsed to extract the ingredient,
    weight, and animal type, and a dose calculation is performed.
    """
    if sub_endpoint == "calculate_dose_rate":
        # Use a regex to extract the required values.
        dose_rate_pattern = re.compile(
            r"calculate (?:the )?dose rate of\s+(.+?)\s*(?:,|in)\s*(?:a\s*)?(\d+)\s*kg\s*(\w+)",
            re.IGNORECASE
        )
        match_obj = dose_rate_pattern.search(request.query)
        if match_obj:
            ingredient_query = match_obj.group(1).strip()
            weight = float(match_obj.group(2).strip())
            animal = match_obj.group(3).strip().lower()
            response, reference = process_pharma_dose_rate(ingredient_query, weight, animal, raw_pharma_docs)
            return {"response": response, "reference": reference}
        else:
            return {"response": "Query does not match dose rate calculation format.", "reference": ""}
    else:
        candidates = hybrid_search(request.query, {"pharma": doc_collections["pharma"]})
        if candidates:
            best_doc = candidates[0]
            full_text = best_doc["text"]
            prompt = create_pharma_prompt(request.query, full_text, sub_endpoint)
            response = get_llm_response(prompt, request.provider)
            reference = "\n\n".join([f"Match {i+1}:\n{cand['text']}" for i, cand in enumerate(candidates)])
        else:
            response = "No relevant pharma data found."
            reference = ""
        return {"response": response, "reference": reference}

# -------------------------
# Run the API
# -------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)
