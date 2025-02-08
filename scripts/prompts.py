import ollama
import os

MODEL_NAME = "llama3.2"
GENI_MODEL_NAME = "gemini-2.0-flash-lite-preview-02-05"

def create_prompt(query: str, full_text: str) -> str:
    prompt = f"""
You are a veterinarian. Based solely on the clinical text provided, answer the question exactly.
Question: {query}

Clinical Text:
{full_text}

Answer:"""
    return prompt

def get_llm_response_ollama(query: str, full_text: str) -> str:
    prompt = create_prompt(query, full_text)
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

def get_llm_response_gemini(query: str, full_text: str, api_key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
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
    prompt = create_prompt(query, full_text)
    response = chat_session.send_message(prompt)
    return response.text.strip()
