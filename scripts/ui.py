import gradio as gr
import re, os
from scripts.prompts import (MODEL_NAME, create_clinical_prompt, create_disease_prompt, create_pharma_prompt, get_llm_response)
from scripts.models import hybrid_search, build_index
from scripts.clinical import load_clinical_documents
from scripts.disease import load_disease_documents
from scripts.pharma import load_pharma_documents

def create_ui():
    # Load document collections
    clinical_docs = load_clinical_documents()
    disease_docs = load_disease_documents()
    pharma_docs = load_pharma_documents()
    
    # Build FAISS indexes
    index_clinical, _ = build_index(clinical_docs, "database/embeddings_clinical.npy")
    index_disease, _ = build_index(disease_docs, "database/embeddings_disease.npy")
    index_pharma, _ = build_index(pharma_docs, "database/embeddings_pharma.npy")
    
    # Group the collections for retrieval
    doc_collections = {
        "clinical": (clinical_docs, index_clinical),
        "disease": (disease_docs, index_disease),
        "pharma": (pharma_docs, index_pharma)
    }
    
    with gr.Blocks(title="VetLLM Chatbot", css="../css/style.css") as demo:
        gr.Markdown("## VetLLM Chatbot - RAG Endpoints")
        with gr.Row():
            provider_dropdown = gr.Dropdown(label="LLM Provider", choices=["Ollama", "Gemini"], value="Ollama")
        
        # ----- Clinical Data Tab -----
        with gr.Tab("Clinical Data"):
            endpoint_dropdown_clinical = gr.Dropdown(
                label="Endpoint", 
                choices=["synonym", "diagnostic_workup", "drug_of_choice", "differential_diagnosis", "line_of_treatment", "prognosis"],
                value="synonym"
            )
            query_input_clinical = gr.Textbox(lines=2, placeholder="Enter clinical query here...", label="Clinical Query")
            output_clinical = gr.Textbox(label="Clinical Response", lines=10)
            ref_clinical = gr.Textbox(label="Matched Clinical Documents", lines=10)
        
            def process_clinical(query, endpoint, provider):
                candidates = hybrid_search(query, {"clinical": doc_collections["clinical"]})
                if candidates:
                    best_doc = candidates[0]
                    full_text = best_doc["text"]
                    prompt = create_clinical_prompt(query, full_text, endpoint)
                    response = get_llm_response(prompt, provider)
                    reference = ""
                    for i, cand in enumerate(candidates):
                        reference += f"Match {i+1}:\n{cand['text']}\n\n"
                else:
                    response, reference = "No relevant clinical data found.", ""
                # Log to developer console via injected HTML
                log_script = f"<script>console.log('Clinical Request:', {repr(query)}, 'Response:', {repr(response)});</script>"
                return response, reference, log_script
            
            query_input_clinical.submit(process_clinical, inputs=[query_input_clinical, endpoint_dropdown_clinical, provider_dropdown], outputs=[output_clinical, ref_clinical, gr.HTML(visible=False)])
            submit_button_clinical = gr.Button("Submit Clinical Query")
            submit_button_clinical.click(process_clinical, inputs=[query_input_clinical, endpoint_dropdown_clinical, provider_dropdown], outputs=[output_clinical, ref_clinical, gr.HTML(visible=False)])
        
        # ----- Disease Symptoms Tab -----
        with gr.Tab("Disease Symptoms"):
            endpoint_dropdown_disease = gr.Dropdown(
                label="Endpoint", 
                choices=["describe_clinical_signs", "symptoms", "reverse_symptom_lookup"],
                value="symptoms"
            )
            query_input_disease = gr.Textbox(lines=2, placeholder="Enter disease query here...", label="Disease Query")
            output_disease = gr.Textbox(label="Disease Response", lines=10)
            ref_disease = gr.Textbox(label="Matched Disease Documents", lines=10)
            
            def process_disease(query, endpoint, provider):
                candidates = hybrid_search(query, {"disease": doc_collections["disease"]})
                if candidates:
                    best_doc = candidates[0]
                    full_text = best_doc["text"]
                    prompt = create_disease_prompt(query, full_text, endpoint)
                    response = get_llm_response(prompt, provider)
                    reference = ""
                    for i, cand in enumerate(candidates):
                        reference += f"Match {i+1}:\n{cand['text']}\n\n"
                else:
                    response, reference = "No relevant disease data found.", ""
                log_script = f"<script>console.log('Disease Request:', {repr(query)}, 'Response:', {repr(response)});</script>"
                return response, reference, log_script
            
            query_input_disease.submit(process_disease, inputs=[query_input_disease, endpoint_dropdown_disease, provider_dropdown], outputs=[output_disease, ref_disease, gr.HTML(visible=False)])
            submit_button_disease = gr.Button("Submit Disease Query")
            submit_button_disease.click(process_disease, inputs=[query_input_disease, endpoint_dropdown_disease, provider_dropdown], outputs=[output_disease, ref_disease, gr.HTML(visible=False)])
        
        # ----- Pharma Tab -----
        with gr.Tab("Pharma"):
            endpoint_dropdown_pharma = gr.Dropdown(
                label="Endpoint", 
                choices=["calculate_dose_rate", "indication", "contraindication", "mechanism_of_action", "metabolism_and_elimination", "products"],
                value="indication"
            )
            query_input_pharma = gr.Textbox(lines=2, placeholder="Enter pharma query here...", label="Pharma Query")
            output_pharma = gr.Textbox(label="Pharma Response", lines=10)
            ref_pharma = gr.Textbox(label="Matched Pharma Documents", lines=10)
            
            def process_pharma(query, endpoint, provider):
                candidates = hybrid_search(query, {"pharma": doc_collections["pharma"]})
                if candidates:
                    best_doc = candidates[0]
                    full_text = best_doc["text"]
                    prompt = create_pharma_prompt(query, full_text, endpoint)
                    response = get_llm_response(prompt, provider)
                    reference = ""
                    for i, cand in enumerate(candidates):
                        reference += f"Match {i+1}:\n{cand['text']}\n\n"
                else:
                    response, reference = "No relevant pharma data found.", ""
                log_script = f"<script>console.log('Pharma Request:', {repr(query)}, 'Response:', {repr(response)});</script>"
                return response, reference, log_script
            
            query_input_pharma.submit(process_pharma, inputs=[query_input_pharma, endpoint_dropdown_pharma, provider_dropdown], outputs=[output_pharma, ref_pharma, gr.HTML(visible=False)])
            submit_button_pharma = gr.Button("Submit Pharma Query")
            submit_button_pharma.click(process_pharma, inputs=[query_input_pharma, endpoint_dropdown_pharma, provider_dropdown], outputs=[output_pharma, ref_pharma, gr.HTML(visible=False)])
        
    return demo
