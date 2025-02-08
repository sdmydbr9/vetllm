import os
import json

def load_clinical_documents(database_path="database/clinical_data.json"):
    with open(database_path, 'r') as f:
        clinical_data = json.load(f)
    
    documents = []
    for case in clinical_data:
        clinical_case = case.get("Clinical Case", {})
        generated_data = case.get("Generated Exam Data", {})
        exam_details = "\n".join([f"{key}: {value}" for key, value in generated_data.get("Clinical Examination", {}).items()])
        diagnostic_details = "\n".join([f"{key}: {value}" for key, value in generated_data.get("Diagnostic Workup", {}).items()])
        treatment_details = "\n".join([f"{key}: {value}" for key, value in generated_data.get("Line of Treatment", {}).items()])
        
        # Include extra keys if available
        other_details = ""
        if "Drug of Choice" in generated_data:
            other_details += f"Drug of Choice: {generated_data.get('Drug of Choice', '')}\n"
        if "Differential Diagnosis" in generated_data:
            other_details += f"Differential Diagnosis: {generated_data.get('Differential Diagnosis', '')}\n"
        
        context = f"""
Disease: {clinical_case.get('Disease', '')}
Synonyms: {clinical_case.get('Synonyms', '')}

Clinical Examination:
{exam_details}

Diagnostic Workup:
{diagnostic_details}

Diagnosis: {generated_data.get('Diagnosis', '')}

{other_details}
Line of Treatment:
{treatment_details}

Prognosis: {generated_data.get('Prognosis', '')}
Client Education & Prevention: {generated_data.get('Client Education & Prevention', '')}
        """
        documents.append(context.strip())
    return documents
