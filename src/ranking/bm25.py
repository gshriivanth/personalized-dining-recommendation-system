# src/ranking/bm25.py
"""
BM25 (Best Matching 25) ranking for food search.

Implements probabilistic IR ranking as described in the professor's Week 3 baseline.
BM25 is considered the state-of-the-art for traditional text retrieval.
"""
from __future__ import annotations

from typing import List, Dict, Tuple
import math
from collections import Counter

from src.logical_view import Food
from src.index.inverted_index import tokenize, KeywordIndex


class BM25Ranker:
    """
    BM25 ranking for food search.
    
    BM25 formula:
    score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))
    
    where:
    - IDF(qi) = log((N - df(qi) + 0.5) / (df(qi) + 0.5))
    - f(qi, D) = term frequency of qi in document D
    - |D| = document length
    - avgdl = average document length
    - k1, b = tuning parameters (typically k1=1.5, b=0.75)
    """
    
    def __init__(
        self,
        keyword_index: KeywordIndex,
        foods: Dict[int, Food],
        k1: float = 1.5,
        b: float = 0.75
    ):
        """
        Initialize BM25 ranker.
        
        Args:
            keyword_index: Keyword inverted index
            foods: Dictionary mapping food_id to Food object
            k1: Term frequency saturation parameter (default 1.5)
            b: Length normalization parameter (default 0.75)
        """
        self.keyword_index = keyword_index
        self.foods = foods
        self.k1 = k1
        self.b = b
        self.num_docs = len(foods)
        
        # Precompute document lengths
        self.doc_lengths: Dict[int, int] = {}
        total_length = 0
        
        for food_id, food in foods.items():
            tokens = tokenize(food.name)
            if food.brand:
                tokens.extend(tokenize(food.brand))
            doc_length = len(tokens)
            self.doc_lengths[food_id] = doc_length
            total_length += doc_length
        
        # Compute average document length
        self.avg_doc_length = total_length / self.num_docs if self.num_docs > 0 else 0.0
    
    def compute_idf(self, term: str) -> float:
        """
        Compute BM25 IDF for a term.
        
        Args:
            term: Query term
        
        Returns:
            IDF score
        """
        doc_freq = len(self.keyword_index.index.get(term, set()))
        
        # BM25 IDF formula
        numerator = self.num_docs - doc_freq + 0.5
        denominator = doc_freq + 0.5
        
        if denominator == 0:
            return 0.0
        
        return math.log((numerator / denominator) + 1.0)
    
    def score_document(self, food_id: int, query_terms: List[str]) -> float:
        """
        Compute BM25 score for a single document.
        
        Args:
            food_id: Document ID to score
            query_terms: List of query terms
        
        Returns:
            BM25 score
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
            
            # Term frequency in document
            tf = term_counts[term]
            
            # Compute IDF
            idf = self.compute_idf(term)
            
            # BM25 formula
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * doc_length / self.avg_doc_length)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def rank(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[Food, float]]:
        """
        Rank documents using BM25.
        
        Args:
            query: Search query
            top_k: Number of top results to return
        
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
            score = self.score_document(food_id, query_terms)
            if score > 0:
                food = self.foods.get(food_id)
                if food:
                    scored_foods.append((food, score))
        
        # Sort by score descending
        scored_foods.sort(key=lambda x: x[1], reverse=True)
        
        return scored_foods[:top_k]
