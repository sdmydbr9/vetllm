// server.js
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import fs from 'fs';

dotenv.config();

const app = express();
const port = process.env.PORT || 6543;

// Set up __dirname for ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ============================================================
// Read configuration from ./public/config.json
// ============================================================
let serverConfig = {};
const configPath = path.join(__dirname, 'public', 'config.json');

try {
  const configFile = fs.readFileSync(configPath, 'utf-8');
  serverConfig = JSON.parse(configFile);
  console.log("Server config loaded:", serverConfig);
} catch (error) {
  console.error("Error reading config.json:", error);
  // Fallback configuration if the file cannot be read
  serverConfig.apiBaseUrl = "https://chat.clinicpaws.com/api";
}

// ============================================================
// Known prompt templates used for routing.
// If the incoming query exactly equals one of these keys,
// we replace it with the full prompt text.
// ============================================================
const promptInfo = {
  "synonym": "Return the disease synonyms for: ",
  "diagnostic_workup": "Return the diagnostic workup for: ",
  "drug_of_choice": "What is the drug of choice for: ",
  "differential_diagnosis": "Return the differential diagnosis for: ",
  "line_of_treatment": "Return the line of treatment for: ",
  "prognosis": "Return the prognosis for: ",
  "describe_clinical_signs": "Describe the clinical signs and symptoms for: ",
  "symptoms": "Return the list of matched diseases for the symptoms: ",
  "reverse_symptom_lookup": "Return the clinical signs and symptoms for disease: ",
  "calculate_dose_rate": "Calculate the dose rate of {ingredient} in a {weight} {species}. ",
  "indication": "Return the indications for the drug: ",
  "contraindication": "Return the contraindications for the drug: ",
  "mechanism_of_action": "Return the mechanism of action for the drug: ",
  "metabolism_and_elimination": "Return the metabolism and elimination details for the drug: ",
  "products": "Return the products for the drug: "
};

/**
 * processQuery uses the REST API endpoints on the Python backend.
 * It accepts a query, provider, category, and endpoint.
 * If the incoming query exactly matches one of our known action keywords,
 * it is normalized by prepending the corresponding prompt text.
 * The endpoint path is dynamically built as `/<category>/<endpoint>`.
 */
async function processQuery(message, provider, category, endpoint) {
  try {
    // Normalize the query if it exactly matches one of our action keywords.
    const lowerQuery = message.trim().toLowerCase();
    if (promptInfo.hasOwnProperty(lowerQuery)) {
      console.log(`Normalizing query "${message}" to "${promptInfo[lowerQuery]}"`);
      message = promptInfo[lowerQuery];
    }

    // Prepare and log the raw request data.
    const requestData = { query: message, endpoint: endpoint, provider: provider };
    console.log("Raw API Request:", requestData);

    // Dynamically build the endpoint path (e.g. /clinical/synonym, /pharma/indication, etc.)
    const endpointPath = `/${category}/${endpoint}`;
    console.log("Using endpoint path:", endpointPath);

    // Call the REST API endpoint using fetch.
    // Use the API base URL from our config.
    const res = await fetch(`${serverConfig.apiBaseUrl}${endpointPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    });

    const result = await res.json();
    console.log("Raw API Response:", result);

    // Assume our FastAPI endpoints return a JSON with keys "response" and "reference"
    let main_response = result.response || "";
    let matches = result.reference || "";

    console.log("Sending response:", { response: main_response, matches: matches });
    return { main_response, matches };
  } catch (error) {
    console.error("Error during API call:", error);
    return { main_response: "Error: " + error.message, matches: "" };
  }
}

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'chat.html'));
});

// Clinical endpoints (e.g., /clinical/synonym, /clinical/line_of_treatment, etc.)
app.post('/clinical/:endpoint', async (req, res) => {
  const endpoint = req.params.endpoint;
  const { message, provider } = req.body;
  console.log(`Received clinical query for endpoint ${endpoint}: "${message}" with provider: ${provider}`);
  const { main_response, matches } = await processQuery(message, provider, "clinical", endpoint);
  res.json({ response: main_response, matches: matches });
});

// Disease endpoints (e.g., /disease/symptoms, /disease/reverse_symptom_lookup, etc.)
app.post('/disease/:endpoint', async (req, res) => {
  const endpoint = req.params.endpoint;
  const { message, provider } = req.body;
  console.log(`Received disease query for endpoint ${endpoint}: "${message}" with provider: ${provider}`);
  const { main_response, matches } = await processQuery(message, provider, "disease", endpoint);
  res.json({ response: main_response, matches: matches });
});

// Pharma endpoints (e.g., /pharma/calculate_dose_rate, /pharma/metabolism_and_elimination, etc.)
app.post('/pharma/:endpoint', async (req, res) => {
  const endpoint = req.params.endpoint;
  const { message, provider } = req.body;
  console.log(`Received pharma query for endpoint ${endpoint}: "${message}" with provider: ${provider}`);
  const { main_response, matches } = await processQuery(message, provider, "pharma", endpoint);
  res.json({ response: main_response, matches: matches });
});

// General fallback chat endpoint.
app.post('/chat', async (req, res) => {
  console.log("Received /chat request:", req.body);
  const { message, provider } = req.body;
  if (!message) {
    return res.status(400).json({ error: 'No message provided' });
  }
  console.log(`Received chat message: "${message}" with provider: ${provider}`);
  // Fallback: use clinical synonyms as default.
  const { main_response, matches } = await processQuery(message, provider, "clinical", "synonym");
  res.json({ response: main_response, matches: matches });
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
