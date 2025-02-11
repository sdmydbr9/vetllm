from dotenv import load_dotenv
import os
load_dotenv()  # load environment variables from .env

MODEL_NAME = "llama3.2"
GENI_MODEL_NAME = "gemini-2.0-flash-lite-preview-02-05"

def create_clinical_prompt(query: str, full_text: str, endpoint: str) -> str:
    instruction_map = {
        "synonym": "Provide synonyms for the disease mentioned in the clinical data.",
        "diagnostic_workup": "Summarize the diagnostic workup from the clinical data.",
        "drug_of_choice": "Identify the drug of choice for the condition in the clinical data.",
        "differential_diagnosis": "List the differential diagnoses based on the clinical data.",
        "line_of_treatment": "Describe the recommended line of treatment from the clinical data.",
        "prognosis": "Describe the prognosis based on the clinical data."
    }
    instruction = instruction_map.get(endpoint, "Answer the query based on the clinical data.")
    prompt = f"""
You are a veterinarian. Based solely on the following clinical data, {instruction}
Query: {query}

Clinical Data:
{full_text}

Answer:"""
    return prompt

def create_disease_prompt(query: str, full_text: str, endpoint: str) -> str:
    instruction_map = {
        "describe_clinical_signs": "Describe the clinical signs associated with the disease symptoms.",
        "symptoms": "List the symptoms mentioned in the disease data.",
        "reverse_symptom_lookup": "Perform a reverse lookup for the given symptom to identify possible diseases."
    }
    instruction = instruction_map.get(endpoint, "Answer the query based on the disease symptoms.")
    prompt = f"""
You are a veterinarian. Based solely on the following disease symptoms data, {instruction}
Query: {query}

Disease Symptoms Data:
{full_text}

Answer:"""
    return prompt

def create_pharma_prompt(query: str, full_text: str, endpoint: str) -> str:
    instruction_map = {
        "calculate_dose_rate": "Calculate the dose rate for the medication based on the provided parameters.",
        "indication": "Describe the indication for the medication.",
        "contraindication": "List the contraindications for the medication.",
        "mechanism_of_action": "Describe the mechanism of action of the medication.",
        "metabolism_and_elimination": "Describe the metabolism and elimination of the medication.",
        "products": "List the products that contain this medication."
    }
    instruction = instruction_map.get(endpoint, "Answer the query based on the pharmaceutical data.")
    prompt = f"""
You are a veterinarian. Based solely on the following pharmaceutical data, {instruction}
Query: {query}

Pharmaceutical Data:
{full_text}

Answer:"""
    return prompt

def get_llm_response_ollama(prompt: str) -> str:
    import ollama
    response = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}])
    if isinstance(response, dict):
        response_text = response.get('text', '') or str(response.get('message', ''))
    elif hasattr(response, "text"):
        response_text = str(response.text)
    elif hasattr(response, "message"):
        response_text = str(response.message)
    else:
        response_text = "No response returned from the LLM."
    return response_text.strip()

def get_llm_response_gemini(prompt: str) -> str:
    import google.generativeai as genai
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        return "Gemini API key not found in environment variables."
    genai.configure(api_key=gemini_api_key)
    generation_config = {
      "temperature": 0,
      "top_p": 0.95,
      "top_k": 64,
      "max_output_tokens": 8192,
      "response_mime_type": "application/json",
    }
    model = genai.GenerativeModel(
      model_name=GENI_MODEL_NAME,
      generation_config=generation_config,
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)
    return response.text.strip()

def get_llm_response(prompt: str, provider: str = "Ollama") -> str:
    if provider == "Gemini":
        return get_llm_response_gemini(prompt)
    else:
        return get_llm_response_ollama(prompt)
