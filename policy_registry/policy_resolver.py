"""
policy_resolver.py - Policy Version Resolution

Resolves policy versions to policy definitions.
Maintains append-only policy registry.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from policy_registry.policy_definition import PolicyDefinition


class PolicyResolver:
    """
    Resolves policy versions to policy definitions.
    
    Maintains an append-only registry of policy definitions.
    """
    
    def __init__(self, registry_dir: str = "policy_registry/policies"):
        """
        Initialize policy resolver.
        
        Args:
            registry_dir: Directory containing policy definition files
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
    
    def save_policy(self, policy: PolicyDefinition) -> str:
        """
        Save policy definition to registry (append-only).
        
        Args:
            policy: Policy definition to save
        
        Returns:
            Policy version identifier
        """
        version = policy.get_version_id()
        
        # Check if policy already exists
        existing = self.load_policy(version)
        if existing:
            # Policy already exists, return existing version
            return version
        
        # Save to file
        policy_file = self.registry_dir / f"{version}.json"
        
        with open(policy_file, 'w') as f:
            json.dump(policy.to_dict(), f, indent=2)
        
        return version
    
    def load_policy(self, version: str) -> Optional[PolicyDefinition]:
        """
        Load policy definition by version.
        
        Args:
            version: Policy version identifier (e.g., "v1_3f8a1b2c")
        
        Returns:
            Policy definition, or None if not found
        """
        policy_file = self.registry_dir / f"{version}.json"
        
        if not policy_file.exists():
            return None
        
        try:
            with open(policy_file, 'r') as f:
                data = json.load(f)
            return PolicyDefinition.from_dict(data)
        except Exception as e:
            print(f"Error loading policy {version}: {e}")
            return None
    
    def list_versions(self) -> List[str]:
        """
        List all policy versions in registry.
        
        Returns:
            List of version identifiers
        """
        versions = []
        for policy_file in self.registry_dir.glob("*.json"):
            version = policy_file.stem
            versions.append(version)
        
        # Sort by version number (if possible)
        try:
            def version_key(v):
                if v.startswith('v'):
                    try:
                        num = int(v[1:].split('_')[0])
                        return (num, v)
                    except:
                        return (999999, v)
                return (999999, v)
            
            versions.sort(key=version_key)
        except:
            versions.sort()
        
        return versions
    
    def get_latest_version(self) -> Optional[str]:
        """
        Get latest policy version.
        
        Returns:
            Latest version identifier, or None if no policies exist
        """
        versions = self.list_versions()
        if not versions:
            return None
        return versions[-1]
    
    def policy_exists(self, version: str) -> bool:
        """
        Check if policy version exists in registry.
        
        Args:
            version: Policy version identifier
        
        Returns:
            True if policy exists, False otherwise
        """
        policy_file = self.registry_dir / f"{version}.json"
        return policy_file.exists()
    
    def get_policy_metadata(self, version: str) -> Optional[Dict]:
        """
        Get policy metadata (without full definition).
        
        Args:
            version: Policy version identifier
        
        Returns:
            Metadata dict, or None if not found
        """
        policy = self.load_policy(version)
        if not policy:
            return None
        
        return {
            'version': policy.version,
            'created_at': policy.created_at,
            'engine_module': policy.engine_module,
            'intent_model_module': policy.intent_model_module,
            'description': policy.description,
            'author': policy.author
        }

