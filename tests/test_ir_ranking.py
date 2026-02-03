# tests/test_ir_ranking.py
"""
Tests for traditional IR ranking algorithms (TF-IDF and BM25).
"""
import pytest
from src.ranking import TFIDFRanker, BM25Ranker, compute_tf, compute_idf
from src.index import KeywordIndex
from src.logical_view import Food


class TestComputeTF:
    """Tests for TF computation."""

    def test_compute_tf_raw(self):
        """Test raw TF."""
        tf = compute_tf(5, 100, "raw")
        assert tf == 5.0

    def test_compute_tf_log(self):
        """Test log-normalized TF."""
        tf = compute_tf(10, 100, "log")
        assert tf > 1.0

    def test_compute_tf_normalized(self):
        """Test length-normalized TF."""
        tf = compute_tf(5, 100, "normalized")
        assert tf == 0.05


class TestComputeIDF:
    """Tests for IDF computation."""

    def test_compute_idf_basic(self):
        """Test basic IDF."""
        idf = compute_idf(1000, 100)
        assert idf > 0

    def test_compute_idf_rare_term(self):
        """Test IDF for rare term."""
        idf = compute_idf(1000, 1)
        assert idf > 2.0

    def test_compute_idf_common_term(self):
        """Test IDF for common term."""
        idf = compute_idf(1000, 500)
        assert idf < 1.0


class TestTFIDFRanker:
    """Tests for TF-IDF ranker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_foods = [
            Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0),
            Food(2, "Grilled Chicken", 150, 30, 0, 3, 0),
            Food(3, "Brown Rice", 370, 7.9, 77.2, 2.9, 3.5),
            Food(4, "Broccoli", 34, 2.8, 7, 0.4, 2.6),
        ]

        # Build keyword index
        self.keyword_index = KeywordIndex()
        for food in self.sample_foods:
            self.keyword_index.add_food(food)

        # Create foods dict
        self.foods_dict = {food.food_id: food for food in self.sample_foods}

        # Create ranker
        self.ranker = TFIDFRanker(self.keyword_index, self.foods_dict)

    def test_ranker_initialization(self):
        """Test ranker initialization."""
        assert self.ranker.num_docs == 4
        assert len(self.ranker.doc_lengths) == 4

    def test_score_document(self):
        """Test scoring a single document."""
        query_terms = ["chicken"]
        score = self.ranker.score_document(1, query_terms)
        assert score > 0

    def test_rank_basic(self):
        """Test basic ranking."""
        results = self.ranker.rank("chicken", top_k=5)
        assert len(results) == 2  # Only 2 foods contain "chicken"
        assert all(isinstance(food, Food) for food, _ in results)
        assert all(isinstance(score, float) for _, score in results)

    def test_rank_descending_order(self):
        """Test that results are sorted by score."""
        results = self.ranker.rank("chicken", top_k=5)
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)


class TestBM25Ranker:
    """Tests for BM25 ranker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_foods = [
            Food(1, "Chicken Breast", 165, 31, 0, 3.6, 0),
            Food(2, "Grilled Chicken", 150, 30, 0, 3, 0),
            Food(3, "Brown Rice", 370, 7.9, 77.2, 2.9, 3.5),
            Food(4, "Broccoli", 34, 2.8, 7, 0.4, 2.6),
        ]

        # Build keyword index
        self.keyword_index = KeywordIndex()
        for food in self.sample_foods:
            self.keyword_index.add_food(food)

        # Create foods dict
        self.foods_dict = {food.food_id: food for food in self.sample_foods}

        # Create ranker
        self.ranker = BM25Ranker(self.keyword_index, self.foods_dict)

    def test_ranker_initialization(self):
        """Test ranker initialization."""
        assert self.ranker.num_docs == 4
        assert len(self.ranker.doc_lengths) == 4
        assert self.ranker.avg_doc_length > 0

    def test_ranker_parameters(self):
        """Test ranker with custom parameters."""
        ranker = BM25Ranker(self.keyword_index, self.foods_dict, k1=2.0, b=0.5)
        assert ranker.k1 == 2.0
        assert ranker.b == 0.5

    def test_compute_idf(self):
        """Test IDF computation."""
        idf = self.ranker.compute_idf("chicken")
        assert idf > 0

    def test_score_document(self):
        """Test scoring a single document."""
        query_terms = ["chicken"]
        score = self.ranker.score_document(1, query_terms)
        assert score > 0

    def test_rank_basic(self):
        """Test basic ranking."""
        results = self.ranker.rank("chicken", top_k=5)
        assert len(results) == 2  # Only 2 foods contain "chicken"
        assert all(isinstance(food, Food) for food, _ in results)
        assert all(isinstance(score, float) for _, score in results)

    def test_rank_descending_order(self):
        """Test that results are sorted by score."""
        results = self.ranker.rank("chicken", top_k=5)
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_rank_empty_query(self):
        """Test ranking with empty query."""
        results = self.ranker.rank("", top_k=5)
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
