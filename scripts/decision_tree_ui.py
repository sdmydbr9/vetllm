import os
import gradio as gr
from gradio_client import Client

# Initialize the Gradio client pointing to your VetLLM chatbot API
client = Client("http://192.168.29.105:7860/")

def load_model(provider: str) -> str:
    """
    Calls the /load_model endpoint.
    Reads the Gemini API key from the environment if provider is Gemini.
    Returns the model status message.
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "") if provider == "Gemini" else ""
    result = client.predict(
        provider=provider,
        gemini_api_key=gemini_api_key,
        api_name="/load_model"
    )
    return result

def process_query(query: str, provider: str):
    """
    Calls the /process_query endpoint.
    Reads the Gemini API key from the environment if needed.
    Returns a tuple (chatbot response, matched documents).
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "") if provider == "Gemini" else ""
    result = client.predict(
        query=query,
        provider=provider,
        gemini_api_key=gemini_api_key,
        api_name="/process_query"
    )
    return result

# Build the Gradio interface using Blocks with custom CSS for a modern, sleek look.
with gr.Blocks(css="""
body {
    background-color: #f0f2f5;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}
.gradio-container {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
}
h1, h2, h3, h4, h5, h6 {
    color: #333333;
}
input, textarea, select {
    border-radius: 8px;
    border: 1px solid #ced4da;
    padding: 10px;
}
button {
    border-radius: 8px;
    background-color: #007bff;
    color: #fff;
    border: none;
    padding: 10px 20px;
}
button:hover {
    background-color: #0056b3;
}
""") as demo:
    
    gr.Markdown("## VetLLM API Frontend")
    
    with gr.Row():
        provider_dropdown = gr.Dropdown(label="LLM Provider", choices=["Ollama", "Gemini"], value="Ollama")
        load_model_button = gr.Button("Load Model")
        load_status = gr.Textbox(label="Model Status", interactive=False)
    
    with gr.Row():
        query_input = gr.Textbox(lines=2, label="Your Question", placeholder="Enter your query here...")
    
    with gr.Row():
        submit_button = gr.Button("Submit Query")
    
    with gr.Row():
        response_output = gr.Textbox(label="Chatbot Response", lines=10)
        matches_output = gr.Textbox(label="Matched Documents (Reference)", lines=10)
    
    # When the user clicks the Load Model button, call the /load_model endpoint.
    load_model_button.click(fn=load_model,
                            inputs=provider_dropdown,
                            outputs=load_status)
    
    # When the user submits a query, call the /process_query endpoint.
    submit_button.click(fn=process_query,
                        inputs=[query_input, provider_dropdown],
                        outputs=[response_output, matches_output])
    
# Pass server_name and server_port to launch(), not Blocks()
demo.launch(server_name="0.0.0.0", server_port=6543)
