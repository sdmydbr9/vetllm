import gradio as gr
import re, os
from scripts.prompts import MODEL_NAME, get_llm_response_ollama, get_llm_response_gemini
from scripts.models import hybrid_search, build_index
from scripts.clinical import load_clinical_documents
from scripts.disease import load_disease_documents
from scripts.pharma import load_pharma_documents, load_pharma_structured_documents, format_pharma

# Save and load Gemini API key locally
def save_gemini_api_key(api_key):
    with open("gemini_api_key.txt", "w") as f:
        f.write(api_key)
    return api_key

def load_gemini_api_key():
    if os.path.exists("gemini_api_key.txt"):
        with open("gemini_api_key.txt", "r") as f:
            return f.read().strip()
    return ""

def process_pharma_dose_rate(ingredient_query, weight, animal, raw_pharma_docs):
    q_lower = ingredient_query.lower().strip()
    query_tokens = q_lower.split()
    for doc in raw_pharma_docs:
        active_ing = doc.get("Active Ingredient", "").lower().strip()
        ing = doc.get("Ingredient", "").lower().strip()
        trade_name = doc.get("Trade Name", "").lower().strip()
        # If the query is a single token, compare it with the first token of each field.
        if len(query_tokens) == 1:
            if (active_ing.split()[0] == query_tokens[0] or
                ing.split()[0] == query_tokens[0] or
                trade_name.split()[0] == query_tokens[0]):
                dose_rate_info = doc.get("pharma_info", {}).get("dose_rate", {})
                dose_rate_str = dose_rate_info.get(animal, None)
                if dose_rate_str is None:
                    return f"No dose rate information available for {animal}.", f"Candidate:\n{format_pharma(doc)}"
                num_match = re.search(r"([\d\.]+)", dose_rate_str)
                if not num_match:
                    return f"Could not parse dose rate value for {animal}.", f"Candidate:\n{format_pharma(doc)}"
                rate = float(num_match.group(1))
                calculated_dose = rate * weight
                response = (
                    f"Calculated dose for '{doc.get('Active Ingredient')}' in a {weight} kg {animal}: "
                    f"{calculated_dose} mg (@{rate} mg/kg)."
                )
                reference = f"Candidate (Exact Match):\n{format_pharma(doc)}"
                return response, reference
        else:
            # For multi-word queries, use substring matching.
            if (q_lower in active_ing or q_lower in ing or q_lower in trade_name):
                dose_rate_info = doc.get("pharma_info", {}).get("dose_rate", {})
                dose_rate_str = dose_rate_info.get(animal, None)
                if dose_rate_str is None:
                    return f"No dose rate information available for {animal}.", f"Candidate:\n{format_pharma(doc)}"
                num_match = re.search(r"([\d\.]+)", dose_rate_str)
                if not num_match:
                    return f"Could not parse dose rate value for {animal}.", f"Candidate:\n{format_pharma(doc)}"
                rate = float(num_match.group(1))
                calculated_dose = rate * weight
                response = (
                    f"Calculated dose for '{doc.get('Active Ingredient')}' in a {weight} kg {animal}: "
                    f"{calculated_dose} mg (@{rate} mg/kg)."
                )
                reference = f"Candidate (Exact Match):\n{format_pharma(doc)}"
                return response, reference
    return "No exact match found for the specified ingredient.", ""

def create_ui():
    # Load documents from the database
    clinical_docs = load_clinical_documents()
    disease_docs = load_disease_documents()
    pharma_docs = load_pharma_documents()
    raw_pharma_docs = load_pharma_structured_documents()

    # Build FAISS indexes (cache files are stored in the database folder)
    index_clinical, _ = build_index(clinical_docs, "database/embeddings_clinical.npy")
    index_disease, _ = build_index(disease_docs, "database/embeddings_disease.npy")
    index_pharma, _ = build_index(pharma_docs, "database/embeddings_pharma.npy")
    
    # Group the document collections for hybrid search
    doc_collections = {
        "clinical": (clinical_docs, index_clinical),
        "disease": (disease_docs, index_disease),
        "pharma": (pharma_docs, index_pharma)
    }
    
    # Build the Gradio interface with custom CSS loaded from the css file.
    with gr.Blocks(title="VetLLM Chatbot", css="../css/style.css") as demo:
        gr.Markdown("## VetLLM Chatbot - Ask Your Veterinary Questions")
        with gr.Row():
            load_button = gr.Button(f"Load Model ({MODEL_NAME})")
            load_status = gr.Textbox(label="Model Status", interactive=False)
        with gr.Row():
            query_input = gr.Textbox(lines=2, placeholder="Enter your query here...", label="Your Question")
        with gr.Row():
            provider_dropdown = gr.Dropdown(label="LLM Provider", choices=["Ollama", "Gemini"], value="Ollama")
            gemini_api_key_input = gr.Textbox(
                label="Gemini API Key", 
                placeholder="Enter your Gemini API key", 
                type="password", 
                value=load_gemini_api_key()
            )
        with gr.Row():
            output_box = gr.Textbox(label="Chatbot Response", lines=10)
            matches_box = gr.Textbox(label="Matched Documents (Reference)", lines=10)
        
        # Function to warm up the model (dummy call)
        def load_model(provider, gemini_api_key):
            if provider == "Gemini":
                if gemini_api_key:
                    save_gemini_api_key(gemini_api_key)
                    _ = get_llm_response_gemini("dummy query", "dummy context", gemini_api_key)
                    return f"Model {MODEL_NAME} (Gemini) loaded and warmed up."
                else:
                    return "Please provide a Gemini API key."
            else:
                _ = get_llm_response_ollama("dummy query", "dummy context")
                return f"Model {MODEL_NAME} (Ollama) loaded and warmed up."
        
        load_button.click(fn=load_model, inputs=[provider_dropdown, gemini_api_key_input], outputs=load_status)
        
        # Function to process user queries:
        def process_query(query, provider, gemini_api_key):
            # Check if the query is a dose rate calculation query.
            dose_rate_pattern = re.compile(
                r"calculate (?:the )?dose rate of\s+(.+?)\s*(?:,|in)\s*(?:a\s*)?(\d+)\s*kg\s*(\w+)",
                re.IGNORECASE
            )
            match_obj = dose_rate_pattern.search(query)
            if match_obj:
                ingredient_query = match_obj.group(1).strip()
                weight = float(match_obj.group(2).strip())
                animal = match_obj.group(3).strip().lower()
                response, reference = process_pharma_dose_rate(ingredient_query, weight, animal, raw_pharma_docs)
                return response, reference
            else:
                # Otherwise use the normal hybrid search across collections.
                candidates = hybrid_search(query, doc_collections)
                if candidates:
                    best_doc = candidates[0]
                    full_text = best_doc["text"]
                    if provider == "Gemini":
                        if not gemini_api_key:
                            return "Please provide a Gemini API key.", ""
                        response = get_llm_response_gemini(query, full_text, gemini_api_key)
                    else:
                        response = get_llm_response_ollama(query, full_text)
                    # Prepare a reference summary of candidate matches.
                    reference = ""
                    for i, cand in enumerate(candidates):
                        reference += (
                            f"Match {i+1} (Hybrid: {cand['hybrid_score']:.3f}, "
                            f"Vector: {cand['vector_score']:.3f}, Fulltext: {cand['fulltext_score']:.3f}):\n"
                        )
                        reference += cand["text"] + "\n\n"
                    return response, reference
                else:
                    return "Sorry, no relevant information was found.", ""
        
        query_input.submit(fn=process_query, inputs=[query_input, provider_dropdown, gemini_api_key_input], outputs=[output_box, matches_box])
        submit_button = gr.Button("Submit Query")
        submit_button.click(fn=process_query, inputs=[query_input, provider_dropdown, gemini_api_key_input], outputs=[output_box, matches_box])
        
    return demo
