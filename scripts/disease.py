import os
import json

def load_disease_documents(database_path="database/disease_symptoms.json"):
    with open(database_path, 'r') as f:
        disease_symptoms = json.load(f)
    
    documents = []
    if isinstance(disease_symptoms, list):
        for item in disease_symptoms:
            text = (
                f"Disease: {item.get('Disease', '')}\n"
                f"Symptoms: {item.get('Symptoms', '')}\n"
                f"Clinical Signs: {item.get('Clinical_Signs', '')}"
            )
            documents.append(text)
    else:
        text = (
            f"Disease: {disease_symptoms.get('Disease', '')}\n"
            f"Symptoms: {disease_symptoms.get('Symptoms', '')}\n"
            f"Clinical Signs: {disease_symptoms.get('Clinical_Signs', '')}"
        )
        documents.append(text)
    return documents
