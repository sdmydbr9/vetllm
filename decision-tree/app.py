import os
import logging
from flask import Flask, render_template, request, jsonify
from gradio_client import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure logging to show debug information (including API requests and responses)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize the Gradio client pointing to your original VetLLM chatbot API.
client = Client("http://192.168.29.105:7860/")

def process_query(query: str, provider: str = "Ollama") -> tuple:
    """
    Sends the query to the original /process_query endpoint.
    Returns a tuple: (main_response, matches)
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "") if provider == "Gemini" else ""
    try:
        logging.debug(f"Sending API request: query='{query}', provider='{provider}'")
        result = client.predict(
            query=query,
            provider=provider,
            gemini_api_key=gemini_api_key,
            api_name="/process_query"
        )
        logging.debug(f"Received API response: {result}")
        if isinstance(result, (list, tuple)) and len(result) == 2:
            main_response, matches = result
        else:
            main_response, matches = result, ""
        return main_response, matches
    except Exception as e:
        logging.exception("Error during API call")
        return f"Error: {str(e)}", ""

# Mapping of each action to a prompt prefix.
prompt_prefixes = {
    'synonym': 'Return the disease synonyms for: ',
    'diagnostic_workup': 'Return the diagnostic workup for: ',
    'drug_of_choice': 'Return the drug of choice for: ',
    'differential_diagnosis': 'Return the differential diagnosis for: ',
    'line_of_treatment': 'Return the line of treatment for: ',
    'prognosis': 'Return the prognosis for: ',
    'describe_clinical_signs': 'Describe the clinical signs and symptoms for: ',
    'symptoms': 'Return the list of matched diseases for the symptoms: ',
    'reverse_symptom_lookup': 'Return the clinical signs and symptoms for disease: ',
    'calculate_dose_rate': 'calculate the dose rate of {ingredient} in a {weight} {species}.',
    'indication': 'Return the indications for the drug: ',
    'contraindication': 'Return the contraindications for the drug: ',
    'mechanism_of_action': 'Return the mechanism of action for the drug: ',
    'metabolism_and_elimination': 'Return the metabolism and elimination details for the drug: ',
    'products': 'Return the products for the drug: '
}

# Define the actions with display names.
actions = {
    'synonym': {'display': 'Synonym'},
    'diagnostic_workup': {'display': 'Diagnostic Workup'},
    'drug_of_choice': {'display': 'Drug of Choice'},
    'differential_diagnosis': {'display': 'Differential Diagnosis'},
    'line_of_treatment': {'display': 'Line of Treatment'},
    'prognosis': {'display': 'Prognosis'},
    'describe_clinical_signs': {'display': 'Describe Clinical Signs and Symptoms'},
    'symptoms': {'display': 'Symptoms'},
    'reverse_symptom_lookup': {'display': 'Reverse Symptom Lookup'},
    'calculate_dose_rate': {'display': 'Calculate Dose Rate'},
    'indication': {'display': 'Indication'},
    'contraindication': {'display': 'Contraindication'},
    'mechanism_of_action': {'display': 'Mechanism of Action'},
    'metabolism_and_elimination': {'display': 'Metabolism and Elimination'},
    'products': {'display': 'Products'}
}

@app.route('/')
def index():
    # Render the new chat.html which contains the interactive chatbot UI
    return render_template('chat.html', actions=actions, prompt_prefixes=prompt_prefixes)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    message = data['message']
    provider = data.get('provider', 'Ollama')
    logging.debug(f"Received chat message: {message} with provider: {provider}")
    response_text, matches = process_query(message, provider=provider)
    return jsonify({'response': response_text, 'matches': matches})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6543, debug=True)
