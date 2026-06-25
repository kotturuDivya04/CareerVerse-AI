# =============================================================================
# modules/plagiarism/plagiarism_engine.py  —  CareerVerse AI
# Semantic similarity engine for the Plagiarism Detector module.
#
# Workflow:
#   1. Tokenise both texts into sentences (NLTK punkt tokeniser)
#   2. Generate sentence embeddings (sentence-transformers all-MiniLM-L6-v2)
#   3. Compute cosine similarity matrix (scikit-learn)
#   4. Collect sentence pairs above the MATCH_THRESHOLD
#   5. Compute overall similarity percentage from matched pairs
#   6. Return structured result dict (shape app.py + plagiarism.js expect)
# =============================================================================

from __future__ import annotations
import nltk
import numpy as np

# Download punkt tokeniser data on first run (silent if already present)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

# Similarity threshold above which two sentences are considered "matched"
MATCH_THRESHOLD = 0.70

# Minimum sentence length (chars) to include in comparison —
# filters out headings, page numbers and single-word lines
MIN_SENTENCE_LEN = 10

# Maximum matched sentences returned in the response
MAX_MATCHES_RETURNED = 50

# Lazy-loaded model (loaded once on first call, not at import time)
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def _tokenise(text: str) -> list[str]:
    """Split text into sentences and filter out very short ones."""
    sentences = nltk.sent_tokenize(text)
    return [s.strip() for s in sentences if len(s.strip()) >= MIN_SENTENCE_LEN]


def _similarity_status(percent: float) -> str:
    if percent >= 60:
        return 'High'
    if percent >= 30:
        return 'Moderate'
    return 'Low'


def _build_summary(percent: float, status: str, matched_count: int) -> str:
    if status == 'High':
        return (
            f"{percent:.1f}% of the content in Document 1 closely matches "
            f"Document 2. {matched_count} sentence-level matches were detected. "
            f"Significant revision or proper citation is strongly recommended."
        )
    if status == 'Moderate':
        return (
            f"{percent:.1f}% similarity was found between the two documents. "
            f"{matched_count} matching sentences were identified. "
            f"Review the matched passages and add citations where appropriate."
        )
    return (
        f"Only {percent:.1f}% similarity was detected between the two documents. "
        f"{matched_count} minor phrase-level match(es) were found. "
        f"The content appears substantially original."
    )


def _build_recommendation(status: str) -> str:
    if status == 'High':
        return (
            "Substantial overlap detected. Rewrite matched sections in your own "
            "words and cite all external sources using the appropriate format "
            "(APA, MLA, IEEE, etc.). Resubmit after revision."
        )
    if status == 'Moderate':
        return (
            "Some matching content was found. Verify that all quoted or paraphrased "
            "material is properly attributed. Consider paraphrasing repeated phrases."
        )
    return (
        "The documents appear to be largely original. "
        "Ensure any minor overlapping phrases are properly cited if they originate "
        "from an external source."
    )


def analyze_plagiarism(text1: str, text2: str) -> dict:
    """
    Compare two plain-text documents and return a structured result dict.

    Returns:
        {
            "similarity_percent": float,
            "status":             "Low" | "Moderate" | "High",
            "matched_sentences":  [
                {"doc1_sentence": str, "doc2_sentence": str, "similarity": float},
                ...
            ],
            "matched_paragraphs": int,
            "words_compared":     int,
            "summary":            str,
            "recommendation":     str,
        }
    """
    sentences1 = _tokenise(text1)
    sentences2 = _tokenise(text2)

    words_compared = len(text1.split()) + len(text2.split())

    if not sentences1 or not sentences2:
        return {
            'similarity_percent': 0.0,
            'status':             'Low',
            'matched_sentences':  [],
            'matched_paragraphs': 0,
            'words_compared':     words_compared,
            'summary':            'Could not extract enough sentences to compare.',
            'recommendation':     'Please check that both documents contain readable text.',
        }

    model = _get_model()

    embeddings1 = model.encode(sentences1, convert_to_numpy=True, show_progress_bar=False)
    embeddings2 = model.encode(sentences2, convert_to_numpy=True, show_progress_bar=False)

    # Cosine similarity matrix: shape (len1, len2)
    from sklearn.metrics.pairwise import cosine_similarity
    sim_matrix = cosine_similarity(embeddings1, embeddings2)

        # Collect matched pairs (one-to-one matching)

    matched_sentences = []
    used_doc2 = set()
    matched_scores = []

    for i in range(len(sentences1)):

        best_j = -1
        best_sim = 0.0

        for j in range(len(sentences2)):

            if j in used_doc2:
                continue

            sim = float(sim_matrix[i][j])

            if sim > best_sim:
                best_sim = sim
                best_j = j

        if best_j != -1 and best_sim >= MATCH_THRESHOLD:

            matched_sentences.append({
                'doc1_sentence': sentences1[i],
                'doc2_sentence': sentences2[best_j],
                'similarity': round(best_sim * 100, 1),
            })

            used_doc2.add(best_j)
            matched_scores.append(best_sim)

    # Sort by similarity
    matched_sentences.sort(
        key=lambda x: x['similarity'],
        reverse=True
    )

    matched_sentences = matched_sentences[:MAX_MATCHES_RETURNED]

    # Improved similarity calculation

    if matched_scores:
        similarity_percent = round(
            (sum(matched_scores) / len(sentences1)) * 100,
            2
        )
    else:
        similarity_percent = 0.0

    matched_paragraphs = (
        max(1, len(matched_sentences) // 5)
        if matched_sentences else 0
    )

    status = _similarity_status(similarity_percent)

    return {
        'similarity_percent': similarity_percent,
        'status': status,
        'matched_sentences': matched_sentences,
        'matched_paragraphs': matched_paragraphs,
        'words_compared': words_compared,
        'summary': _build_summary(
            similarity_percent,
            status,
            len(matched_sentences)
        ),
        'recommendation': _build_recommendation(status),
    }