# src/ranking/tfidf.py
"""
TF-IDF (Term Frequency-Inverse Document Frequency) ranking for food search.

Implements traditional IR ranking as described in the professor's Week 3 baseline.
"""
from __future__ import annotations

from typing import List, Dict, Tuple
import math
from collections import Counter

from src.logical_view import Food
from src.index.inverted_index import tokenize, KeywordIndex


def compute_tf(term_freq: int, doc_length: int, normalization: str = "log") -> float:
    """
    Compute term frequency component.
    
    Args:
        term_freq: Raw term frequency in document
        doc_length: Total terms in document
        normalization: "raw", "log", or "normalized"
    
    Returns:
        TF score
    """
    if normalization == "raw":
        return float(term_freq)
    elif normalization == "log":
        return 1.0 + math.log10(term_freq) if term_freq > 0 else 0.0
    elif normalization == "normalized":
        return term_freq / doc_length if doc_length > 0 else 0.0
    else:
        raise ValueError(f"Unknown normalization: {normalization}")


def compute_idf(num_docs: int, doc_freq: int) -> float:
    """
    Compute inverse document frequency.
    
    Args:
        num_docs: Total number of documents in collection
        doc_freq: Number of documents containing the term
    
    Returns:
        IDF score
    """
    if doc_freq == 0:
        return 0.0
    return math.log10(num_docs / doc_freq)


class TFIDFRanker:
    """
    TF-IDF ranking for food search.
    """
    
    def __init__(self, keyword_index: KeywordIndex, foods: Dict[int, Food]):
        """
        Initialize TF-IDF ranker.
        
        Args:
            keyword_index: Keyword inverted index
            foods: Dictionary mapping food_id to Food object
        """
        self.keyword_index = keyword_index
        self.foods = foods
        self.num_docs = len(foods)
        
        # Precompute document lengths (number of terms in each food name + brand)
        self.doc_lengths: Dict[int, int] = {}
        for food_id, food in foods.items():
            tokens = tokenize(food.name)
            if food.brand:
                tokens.extend(tokenize(food.brand))
            self.doc_lengths[food_id] = len(tokens)
    
    def score_document(
        self,
        food_id: int,
        query_terms: List[str],
        tf_normalization: str = "log"
    ) -> float:
        """
        Compute TF-IDF score for a single document.
        
        Args:
            food_id: Document ID to score
            query_terms: List of query terms
            tf_normalization: TF normalization method
        
        Returns:
            TF-IDF score
        """
        food = self.foods.get(food_id)
        if not food:
            return 0.0
        
        # Get document terms
        doc_tokens = tokenize(food.name)
        if food.brand:
            doc_tokens.extend(tokenize(food.brand))
        
        term_counts = Counter(doc_tokens)
        doc_length = self.doc_lengths.get(food_id, len(doc_tokens))
        
        score = 0.0
        for term in query_terms:
            # Skip terms not in document
            if term not in term_counts:
                continue
            
            # Compute TF
            tf = compute_tf(term_counts[term], doc_length, tf_normalization)
            
            # Compute IDF
            doc_freq = len(self.keyword_index.index.get(term, set()))
            idf = compute_idf(self.num_docs, doc_freq)
            
            # Add to score
            score += tf * idf
        
        return score
    
    def rank(
        self,
        query: str,
        top_k: int = 10,
        tf_normalization: str = "log"
    ) -> List[Tuple[Food, float]]:
        """
        Rank documents using TF-IDF.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            tf_normalization: TF normalization method
        
        Returns:
            List of (Food, score) tuples, sorted by score descending
        """
        query_terms = tokenize(query)
        if not query_terms:
            return []
        
        # Get candidate documents (documents containing at least one query term)
        candidate_ids = self.keyword_index.search(query)
        
        # Score each candidate
        scored_foods = []
        for food_id in candidate_ids:
            score = self.score_document(food_id, query_terms, tf_normalization)
            if score > 0:
                food = self.foods.get(food_id)
                if food:
                    scored_foods.append((food, score))
        
        # Sort by score descending
        scored_foods.sort(key=lambda x: x[1], reverse=True)
        
        return scored_foods[:top_k]
