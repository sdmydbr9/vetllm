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

# Set up spaCy and PhraseMatcher for simple keyword matching
nlp = spacy.load("en_core_web_sm")
pharma_keywords = [
    "indication", "tradename", "brand name", "active ingredient", "dose rate",
    "dosage", "administration", "contraindication", "food timing",
    "meal timing", "when shall i give", "mechanism", "mechanism of action", "products",
    "medications", "drugs"
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
    Expects doc_collections as a dict with keys "clinical", "disease", "pharma".
    Each value is a tuple: (list_of_documents, corresponding_FAISS_index)
    """
    category = determine_category_spacy(query)
    print(f"Query routed to category: {category}")
    if category == "pharma":
        docs, index_obj = doc_collections["pharma"]
    elif category == "disease":
        docs, index_obj = doc_collections["disease"]
    else:
        docs, index_obj = doc_collections["clinical"]
    
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
        ft_score = simple_fulltext_score(query, doc)
        if ft_score > 0:
            fulltext_candidates.append({
                "id": i,
                "text": doc,
                "fulltext_score": ft_score,
            })
    
    # Merge candidates and compute a hybrid score
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
    for cand in candidates.values():
        cand["hybrid_score"] = alpha * cand["vector_score"] + (1 - alpha) * cand["fulltext_score"]
    
    sorted_candidates = sorted(candidates.values(), key=lambda x: x["hybrid_score"], reverse=True)
    top_cands = sorted_candidates[:top_candidates]
    return top_cands
