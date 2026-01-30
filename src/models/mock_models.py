"""
Mock ML models for development

These are placeholder models that will be replaced with real models from STEP teams
"""

import numpy as np


class MockXGBoostModel:
    """
    Mock XGBoost that returns random predictions

    This simulates a yield prediction model for Stage 1
    """

    def predict(self, X):
        """
        Predict yield for wafers

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Array of yield predictions (0.4 to 0.95)
        """
        # Return random yield between 0.4 and 0.95
        np.random.seed(42)
        return np.random.uniform(0.4, 0.95, size=len(X))

    def predict_proba(self, X):
        """
        Predict probability distributions

        Returns:
            Array of probability scores
        """
        predictions = self.predict(X)
        # Convert to probability-like format
        return np.column_stack([1 - predictions, predictions])


class MockCNNModel:
    """
    Mock CNN for wafermap pattern classification

    This simulates a pattern recognition model for Stage 2B
    """

    def predict(self, X):
        """
        Predict wafermap pattern type

        Args:
            X: Feature matrix or image data

        Returns:
            Array of pattern classifications
        """
        np.random.seed(42)
        patterns = ['Edge-Ring', 'Center', 'Random']
        # Bias towards Random (most common)
        probabilities = [0.2, 0.2, 0.6]
        return np.random.choice(patterns, size=len(X), p=probabilities)

    def predict_proba(self, X):
        """
        Predict pattern probabilities

        Returns:
            Array of probability distributions for [Edge-Ring, Center, Random]
        """
        np.random.seed(42)
        n_samples = len(X)
        # Generate random probabilities that sum to 1
        probs = np.random.dirichlet([1, 1, 1], size=n_samples)
        return probs


class MockResNetModel:
    """
    Mock ResNet for SEM defect classification

    This simulates a defect detection model for Stage 3
    """

    def predict(self, X):
        """
        Predict defect type from SEM images

        Args:
            X: Image feature matrix

        Returns:
            Array of defect classifications
        """
        np.random.seed(42)
        defect_types = ['Particle', 'Scratch', 'Residue']
        # Roughly even distribution
        probabilities = [0.4, 0.2, 0.4]
        return np.random.choice(defect_types, size=len(X), p=probabilities)

    def predict_proba(self, X):
        """
        Predict defect type probabilities

        Returns:
            Array of probability distributions for [Particle, Scratch, Residue]
        """
        np.random.seed(42)
        n_samples = len(X)
        # Generate random probabilities that sum to 1
        probs = np.random.dirichlet([2, 1, 2], size=n_samples)
        return probs
