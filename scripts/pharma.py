import os
import json

def load_pharma_documents(database_path="database/pharma.json"):
    """
    Loads the pharma data from the JSON file and returns a list of formatted strings.
    Each string includes the following fields:
      - Active Ingredient
      - Trade Name
      - Ingredient
      - Dose Rate
      - Indication
      - Contraindication
      - Food Timing
      - Mechanism
      - Metabolism and Elimination
      - Products
    """
    with open(database_path, 'r') as f:
        pharma_data = json.load(f)

    documents = []

    def format_pharma(item):
        pharma_info = item.get("pharma_info", {})
        text = (
            f"Active Ingredient: {item.get('Active Ingredient', '')}\n"
            f"Trade Name: {item.get('Trade Name', '')}\n"
            f"Ingredient: {item.get('Ingredient', '')}\n"
            f"Dose Rate: {pharma_info.get('dose_rate', '')}\n"
            f"Indication: {pharma_info.get('indication', '')}\n"
            f"Contraindication: {pharma_info.get('contraindication', '')}\n"
            f"Food Timing: {pharma_info.get('food_timing', '')}\n"
            f"Mechanism: {pharma_info.get('mechanism_of_action', '')}\n"
            f"Metabolism and Elimination: {pharma_info.get('metabolism_and_elimination', '')}\n"
            f"Products: {pharma_info.get('products', '')}"
        )
        return text

    if isinstance(pharma_data, list):
        for item in pharma_data:
            documents.append(format_pharma(item))
    else:
        documents.append(format_pharma(pharma_data))

    return documents

def load_pharma_structured_documents(database_path="database/pharma.json"):
    """
    Loads the pharma data from the JSON file and returns it as a list of dictionaries.
    This is useful for precise matching or calculations.
    """
    with open(database_path, 'r') as f:
        pharma_data = json.load(f)
    if isinstance(pharma_data, list):
        return pharma_data
    else:
        return [pharma_data]

def format_pharma(item):
    """
    Returns a formatted string representation of a pharma document.
    Now includes the "metabolism_and_elimination" field.
    """
    pharma_info = item.get("pharma_info", {})
    text = (
        f"Active Ingredient: {item.get('Active Ingredient', '')}\n"
        f"Trade Name: {item.get('Trade Name', '')}\n"
        f"Ingredient: {item.get('Ingredient', '')}\n"
        f"Dose Rate: {pharma_info.get('dose_rate', '')}\n"
        f"Indication: {pharma_info.get('indication', '')}\n"
        f"Contraindication: {pharma_info.get('contraindication', '')}\n"
        f"Food Timing: {pharma_info.get('food_timing', '')}\n"
        f"Mechanism: {pharma_info.get('mechanism_of_action', '')}\n"
        f"Metabolism and Elimination: {pharma_info.get('metabolism_and_elimination', '')}\n"
        f"Products: {pharma_info.get('products', '')}"
    )
    return text
