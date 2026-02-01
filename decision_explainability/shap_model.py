"""
SHAP-style explainability model for decision traces.

Uses a lightweight surrogate model to compute feature importance
for simulated decisions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Use simple logistic regression as surrogate model
# (No sklearn dependency - implement simple version)
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeClassifier
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    # Fallback: simple logistic regression implementation
    pass


@dataclass
class SHAPValues:
    """SHAP values for a single decision."""
    feature_contributions: Dict[str, float]  # feature_name -> contribution
    base_value: float  # Expected value without features
    decision: str  # "CONTINUE" or "DROP"
    
    def to_dict(self) -> Dict:
        return {
            'feature_contributions': self.feature_contributions,
            'base_value': float(self.base_value),
            'decision': self.decision
        }


class DecisionSurrogateModel:
    """
    Lightweight surrogate model for explaining decisions.
    
    Uses logistic regression as a simple, interpretable surrogate
    to approximate the decision function.
    """
    
    def __init__(self, use_tree: bool = False):
        """
        Initialize surrogate model.
        
        Args:
            use_tree: If True, use decision tree. If False, use logistic regression.
        """
        self.use_tree = use_tree
        self.model = None
        self.feature_names = None
        self.is_fitted = False
        
        if not HAS_SKLEARN:
            raise ImportError("sklearn is required for SHAP computation. Install with: pip install scikit-learn")
    
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]):
        """
        Fit surrogate model to decision data.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary outcomes (1 = CONTINUE, 0 = DROP)
            feature_names: Names of features
        """
        if X.shape[1] != len(feature_names):
            raise ValueError(f"Feature count mismatch: X has {X.shape[1]} features, but {len(feature_names)} names provided")
        
        self.feature_names = feature_names
        
        if self.use_tree:
            from sklearn.tree import DecisionTreeClassifier
            self.model = DecisionTreeClassifier(max_depth=5, random_state=42)
        else:
            from sklearn.linear_model import LogisticRegression
            self.model = LogisticRegression(random_state=42, max_iter=1000)
        
        self.model.fit(X, y)
        self.is_fitted = True
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict_proba(X)
    
    def compute_shap_values_simple(self, X: np.ndarray) -> np.ndarray:
        """
        Compute simple SHAP-like values using linear model coefficients.
        
        For logistic regression, coefficients are directly interpretable.
        For trees, uses a simplified approximation.
        
        Returns:
            Array of SHAP values (n_samples, n_features)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before SHAP computation")
        
        if self.use_tree:
            # Simplified: use feature importances as approximation
            importances = self.model.feature_importances_
            # For each sample, scale by prediction difference from mean
            proba = self.model.predict_proba(X)[:, 1]  # CONTINUE probability
            mean_proba = np.mean(proba)
            shap_values = (proba[:, np.newaxis] - mean_proba) * importances[np.newaxis, :]
            return shap_values
        else:
            # For logistic regression: coefficients * (feature - mean_feature)
            # This is a simplified SHAP approximation
            coef = self.model.coef_[0]
            intercept = self.model.intercept_[0]
            
            # Compute baseline (all features at mean)
            X_mean = np.mean(X, axis=0)
            baseline_prob = 1 / (1 + np.exp(-(intercept + np.dot(coef, X_mean))))
            
            # SHAP values: contribution of each feature
            shap_values = np.zeros_like(X)
            for i in range(X.shape[0]):
                # For each feature, compute marginal contribution
                prob = self.model.predict_proba(X[i:i+1])[0, 1]
                for j in range(X.shape[1]):
                    # Set feature j to mean, compute new prob
                    X_perm = X[i].copy()
                    X_perm[j] = X_mean[j]
                    prob_perm = self.model.predict_proba(X_perm.reshape(1, -1))[0, 1]
                    shap_values[i, j] = prob - prob_perm
            
            return shap_values


def prepare_decision_features(traces: List[Dict]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix from decision traces.
    
    Args:
        traces: List of trace dictionaries with state_before and forces_applied
    
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Binary outcomes (1 = CONTINUE, 0 = DROP)
        feature_names: List of feature names
    """
    feature_names = [
        'cognitive_energy',
        'risk_tolerance',
        'effort_tolerance',
        'intent_strength',
        'trust_baseline',
        'value_expectation',
        'step_effort_force',
        'step_risk_force',
        'step_value_force',
        'step_trust_force',
        'step_intent_mismatch'
    ]
    
    X_list = []
    y_list = []
    
    for trace in traces:
        state = trace.get('state_before', {})
        forces = trace.get('forces_applied', {})
        decision = trace.get('decision', 'DROP')
        
        # Extract features
        features = [
            state.get('cognitive_energy', 0.0),
            state.get('risk_tolerance', 0.0),
            state.get('effort_tolerance', 0.0),
            state.get('intent_strength', 0.0),
            state.get('trust_baseline', 0.0),
            state.get('value_expectation', 0.0),
            forces.get('effort', 0.0),
            forces.get('risk', 0.0),
            forces.get('value', 0.0),
            forces.get('trust', 0.0),
            forces.get('intent_mismatch', 0.0)
        ]
        
        X_list.append(features)
        
        # Binary outcome: CONTINUE = 1, DROP = 0
        y_list.append(1 if decision == 'CONTINUE' else 0)
    
    X = np.array(X_list)
    y = np.array(y_list)
    
    return X, y, feature_names


def compute_shap_values_for_decision(
    trace: Dict,
    model: DecisionSurrogateModel,
    feature_names: List[str]
) -> SHAPValues:
    """
    Compute SHAP values for a single decision trace.
    
    Args:
        trace: Single trace dictionary
        model: Fitted surrogate model
        feature_names: List of feature names
    
    Returns:
        SHAPValues object
    """
    # Prepare single sample
    state = trace.get('state_before', {})
    forces = trace.get('forces_applied', {})
    
    features = np.array([[
        state.get('cognitive_energy', 0.0),
        state.get('risk_tolerance', 0.0),
        state.get('effort_tolerance', 0.0),
        state.get('intent_strength', 0.0),
        state.get('trust_baseline', 0.0),
        state.get('value_expectation', 0.0),
        forces.get('effort', 0.0),
        forces.get('risk', 0.0),
        forces.get('value', 0.0),
        forces.get('trust', 0.0),
        forces.get('intent_mismatch', 0.0)
    ]])
    
    # Compute SHAP values
    shap_array = model.compute_shap_values_simple(features)
    shap_values_dict = {
        feature_names[i]: float(shap_array[0, i])
        for i in range(len(feature_names))
    }
    
    # Compute base value (mean prediction)
    # For simplicity, use model intercept as approximation
    if hasattr(model.model, 'intercept_'):
        base_value = float(model.model.intercept_[0])
    else:
        base_value = 0.0
    
    decision = trace.get('decision', 'DROP')
    
    return SHAPValues(
        feature_contributions=shap_values_dict,
        base_value=base_value,
        decision=decision
    )

