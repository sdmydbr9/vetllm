import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import spacy
from spacy.matcher import PhraseMatcher

# Load the encoder (used for all document embeddings)
encoder = SentenceTransformer('paraphrase-mpnet-base-v2')

def build_index(doc_list, cache_filename):
    if os.path.exists(cache_filename):
        print(f"Loading cached embeddings from {cache_filename}...")
        embeddings = np.load(cache_filename)
    else:
        print("Computing embeddings...")
        embeddings = encoder.encode(doc_list, convert_to_numpy=True).astype('float32')
        np.save(cache_filename, embeddings)
        print("Embeddings computed and cached.")
    dimension = embeddings.shape[1]
    index_obj = faiss.IndexFlatL2(dimension)
    index_obj.add(embeddings)
    print(f"FAISS Index built with {index_obj.ntotal} documents.")
    return index_obj, embeddings

def simple_fulltext_score(query: str, doc: str) -> float:
    query_tokens = set(query.lower().split())
    doc_tokens = set(doc.lower().split())
    if not query_tokens:
        return 0.0
    return len(query_tokens.intersection(doc_tokens)) / len(query_tokens)

def progressive_condition_score(query: str, doc: str) -> float:
    """
    Extracts the condition from the document (assumed to be in the line starting with "Disease:")
    and computes a score based on the longest common prefix of tokens.
    For example, if the query is "canine oral" and the condition is "canine oral plasmacytoma",
    the score will be 1.0 (if both tokens match). If the condition is "canine parvovirus",
    only the first token matches, and the score will be 0.5.
    """
    lines = doc.splitlines()
    disease_line = None
    for line in lines:
        if line.strip().lower().startswith("disease:"):
            disease_line = line
            break
    if not disease_line:
        return 0.0
    # Remove the "Disease:" prefix and split into tokens.
    condition = disease_line.split(":", 1)[1].strip().lower()
    query_tokens = query.lower().split()
    condition_tokens = condition.split()
    match_count = 0
    for qt, ct in zip(query_tokens, condition_tokens):
        if qt == ct:
            match_count += 1
        else:
            break
    return match_count / len(query_tokens)

# Set up spaCy and PhraseMatcher for simple keyword matching
nlp = spacy.load("en_core_web_sm")
pharma_keywords = [
    "indication", "tradename", "brand name", "active ingredient", "dose rate",
    "dosage", "administration", "contraindication", "food timing",
    "meal timing", "mechanism", "mechanism of action", "products"
]
clinical_keywords = [
    "line of treatment", "treatment plan", "treatment protocol", "synonyms",
    "drug of choice", "preferred drug", "differential diagnosis",
    "diagnostic differentials", "management"
]
disease_keywords = [
    "symptoms", "clinical signs", "manifestations", "presentation",
    "signs and symptoms", "symptomatology"
]

matcher = PhraseMatcher(nlp.vocab)
def add_patterns(label: str, keywords: list):
    patterns = [nlp(keyword) for keyword in keywords]
    matcher.add(label, patterns)

add_patterns("pharma", pharma_keywords)
add_patterns("clinical", clinical_keywords)
add_patterns("disease", disease_keywords)

def determine_category_spacy(query: str) -> str:
    doc = nlp(query.lower())
    matches = matcher(doc)
    counts = {"pharma": 0, "clinical": 0, "disease": 0}
    for match_id, start, end in matches:
        category = nlp.vocab.strings[match_id]
        counts[category] += 1
    if all(v == 0 for v in counts.values()):
        return "clinical"
    return max(counts, key=counts.get)

def hybrid_search(query: str, doc_collections: dict, top_k_vector: int = 3, top_candidates: int = 5, alpha: float = 0.5):
    """
    Expects doc_collections as a dict. Typically with keys "clinical", "disease", "pharma".
    Each value is a tuple: (list_of_documents, corresponding_FAISS_index)

    If the determined category (via spaCy) is not found in doc_collections,
    then the function falls back to using the first (or only) key provided.
    """
    category = determine_category_spacy(query)
    if category in doc_collections:
        docs, index_obj = doc_collections[category]
    else:
        key = list(doc_collections.keys())[0]
        # Update category to the fallback key
        category = key
        docs, index_obj = doc_collections[key]
    print(f"Query routed to category: {category}")
    
    query_vector = encoder.encode([query], convert_to_numpy=True).astype('float32')
    distances, indices = index_obj.search(query_vector, top_k_vector)
    vector_candidates = []
    for dist, idx in zip(distances[0], indices[0]):
        doc_text = docs[idx]
        vec_sim = 1 / (1 + dist)
        vector_candidates.append({
            "id": idx,
            "text": doc_text,
            "vector_score": vec_sim,
        })
    
    fulltext_candidates = []
    for i, doc in enumerate(docs):
        # Use progressive condition scoring for disease category, otherwise simple scoring.
        if category == "disease":
            ft_score = progressive_condition_score(query, doc)
        else:
            ft_score = simple_fulltext_score(query, doc)
        if ft_score > 0:
            fulltext_candidates.append({
                "id": i,
                "text": doc,
                "fulltext_score": ft_score,
            })
    
    # Merge vector and fulltext candidates.
    candidates = {}
    for cand in vector_candidates:
        candidates[cand["id"]] = {
            "id": cand["id"],
            "text": cand["text"],
            "vector_score": cand["vector_score"],
            "fulltext_score": 0.0
        }
    for cand in fulltext_candidates:
        if cand["id"] in candidates:
            candidates[cand["id"]]["fulltext_score"] = cand["fulltext_score"]
        else:
            candidates[cand["id"]] = {
                "id": cand["id"],
                "text": cand["text"],
                "vector_score": 0.0,
                "fulltext_score": cand["fulltext_score"],
            }
    # Compute the final hybrid score.
    for cand in candidates.values():
        cand["hybrid_score"] = alpha * cand["vector_score"] + (1 - alpha) * cand["fulltext_score"]
    
    sorted_candidates = sorted(candidates.values(), key=lambda x: x["hybrid_score"], reverse=True)
    top_cands = sorted_candidates[:top_candidates]
    return top_cands

def format_pharma(item):
    """
    Returns a formatted string representation of a pharma document.
    Now includes the key "metabolism_and_elimination" if available.
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
