"""
get_current_policy.py - Get Current Policy Version

Utility to get or create current policy version from system state.
"""

from typing import Optional
from policy_registry.policy_definition import create_policy_snapshot
from policy_registry.policy_resolver import PolicyResolver


def get_current_policy_version(
    calibrated_parameters: Optional[dict] = None,
    calibration_file: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Get or create current policy version from system state.
    
    This function:
    1. Creates a policy snapshot from current system state
    2. Checks if an identical policy already exists
    3. Returns existing version if found, otherwise creates new one
    
    Args:
        calibrated_parameters: Optional calibrated parameters dict
        calibration_file: Optional calibration file path
        description: Optional description for new policy
    
    Returns:
        Policy version identifier (e.g., "v1_3f8a1b2c")
    """
    resolver = PolicyResolver()
    
    # Create snapshot of current policy
    policy = create_policy_snapshot(
        calibrated_parameters=calibrated_parameters,
        calibration_file=calibration_file,
        description=description
    )
    
    # Check if identical policy exists (by hash)
    policy_hash = policy.compute_hash()
    
    # List all existing policies and check hashes
    existing_versions = resolver.list_versions()
    for version in existing_versions:
        existing_policy = resolver.load_policy(version)
        if existing_policy and existing_policy.compute_hash() == policy_hash:
            # Identical policy exists, return existing version
            return version
    
    # No identical policy exists, save new one
    version = resolver.save_policy(policy)
    return version


def ensure_policy_version_exists(version: str) -> bool:
    """
    Ensure a policy version exists, creating it if necessary.
    
    Args:
        version: Policy version identifier
    
    Returns:
        True if policy exists (or was created), False on error
    """
    resolver = PolicyResolver()
    
    if resolver.policy_exists(version):
        return True
    
    # Try to create from current state (this is a fallback)
    # In practice, policies should be created explicitly
    try:
        policy = create_policy_snapshot()
        resolver.save_policy(policy)
        return resolver.policy_exists(version)
    except:
        return False

