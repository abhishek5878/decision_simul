"""
policy_definition.py - Policy Definition Structure

A policy definition is an immutable snapshot of the behavioral rules,
intent logic, parameter bounds, and engine code path that generates decisions.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import json


@dataclass
class PolicyDefinition:
    """
    Immutable policy definition snapshot.
    
    Captures everything needed to reproduce decisions:
    - Behavioral equations (via engine identifier)
    - Intent logic (via intent model identifier)
    - Parameter bounds and defaults
    - Engine code path
    - Timestamp of creation
    """
    # Policy identity
    version: str  # e.g., "v1_3f8a1b2c"
    created_at: str  # ISO timestamp
    
    # Behavioral engine
    engine_module: str  # e.g., "behavioral_engine_intent_aware"
    intent_model_module: str  # e.g., "dropsim_intent_model"
    engine_commit_hash: Optional[str] = None  # Git commit if available
    intent_model_commit_hash: Optional[str] = None
    
    # Parameters (bounds and defaults)
    parameter_bounds: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Format: {"BASE_COMPLETION_RATE": {"min": 0.05, "max": 0.90, "default": 0.60}}
    
    # Calibration (if applied)
    calibrated_parameters: Optional[Dict[str, float]] = None
    calibration_file: Optional[str] = None
    
    # Metadata
    description: Optional[str] = None
    author: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PolicyDefinition':
        """Create from dict."""
        return cls(**data)
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash of policy definition.
        
        Uses all fields except version and metadata (which are derived from content).
        """
        # Create hashable representation (excluding version, created_at, description, author)
        hash_data = {
            'engine_module': self.engine_module,
            'engine_commit_hash': self.engine_commit_hash,
            'intent_model_module': self.intent_model_module,
            'intent_model_commit_hash': self.intent_model_commit_hash,
            'parameter_bounds': self.parameter_bounds,
            'calibrated_parameters': self.calibrated_parameters,
            'calibration_file': self.calibration_file
        }
        
        # Sort keys for deterministic hashing
        hash_str = json.dumps(hash_data, sort_keys=True)
        
        # Compute SHA256 hash
        hash_obj = hashlib.sha256(hash_str.encode('utf-8'))
        return hash_obj.hexdigest()[:8]  # First 8 chars for readability
    
    def get_version_id(self) -> str:
        """
        Get version identifier (includes hash for uniqueness).
        
        Format: v{N}_{hash}
        """
        if '_' in self.version and len(self.version.split('_')) == 2:
            # Already has format vN_hash
            return self.version
        
        # Extract version number if possible
        version_num = 1
        if self.version.startswith('v'):
            try:
                version_num = int(self.version[1:].split('_')[0])
            except:
                pass
        
        hash_suffix = self.compute_hash()
        return f"v{version_num}_{hash_suffix}"


def create_policy_snapshot(
    engine_module: str = "behavioral_engine_intent_aware",
    intent_model_module: str = "dropsim_intent_model",
    parameter_bounds: Optional[Dict] = None,
    calibrated_parameters: Optional[Dict] = None,
    calibration_file: Optional[str] = None,
    description: Optional[str] = None,
    author: Optional[str] = None
) -> PolicyDefinition:
    """
    Create a policy snapshot from current system state.
    
    This captures the current policy configuration as an immutable snapshot.
    """
    # Load parameter bounds if not provided
    if parameter_bounds is None:
        try:
            from calibration.parameter_space import PARAMETER_SPACE
            parameter_bounds = {
                name: {
                    'min': param_def.min_value,
                    'max': param_def.max_value,
                    'default': param_def.default
                }
                for name, param_def in PARAMETER_SPACE.items()
            }
        except:
            parameter_bounds = {}
    
    # Create policy definition
    policy = PolicyDefinition(
        version="",  # Will be computed
        created_at=datetime.now().isoformat(),
        engine_module=engine_module,
        intent_model_module=intent_model_module,
        parameter_bounds=parameter_bounds,
        calibrated_parameters=calibrated_parameters,
        calibration_file=calibration_file,
        description=description,
        author=author
    )
    
    # Compute version with hash
    hash_suffix = policy.compute_hash()
    
    # Determine version number (check existing policies)
    try:
        from policy_registry.policy_resolver import PolicyResolver
        resolver = PolicyResolver()
        existing_versions = resolver.list_versions()
        if existing_versions:
            # Get highest version number
            max_version = 0
            for v in existing_versions:
                if v.startswith('v'):
                    try:
                        num = int(v[1:].split('_')[0])
                        max_version = max(max_version, num)
                    except:
                        pass
            version_num = max_version + 1
        else:
            version_num = 1
    except:
        version_num = 1
    
    policy.version = f"v{version_num}_{hash_suffix}"
    
    return policy

