"""
policy_auditor.py - Policy-Trace Consistency Validation

Validates that DecisionTraces are consistent with their policy versions.
Ensures trace-policy integrity.
"""

from typing import Dict, List, Optional
from policy_registry.policy_resolver import PolicyResolver
from policy_registry.policy_definition import PolicyDefinition
from decision_graph.decision_trace import DecisionTrace


class PolicyAuditor:
    """
    Audits trace-policy consistency.
    
    Validates that:
    1. Every trace has a valid policy_version
    2. Policy versions exist in registry
    3. Traces are consistent with their policy definitions
    """
    
    def __init__(self, resolver: Optional[PolicyResolver] = None):
        """
        Initialize policy auditor.
        
        Args:
            resolver: Policy resolver (creates new one if not provided)
        """
        self.resolver = resolver or PolicyResolver()
    
    def validate_trace(self, trace: DecisionTrace) -> Dict:
        """
        Validate a single trace against its policy version.
        
        Args:
            trace: DecisionTrace to validate
        
        Returns:
            Validation result dict with:
            - valid: bool
            - errors: List[str]
            - warnings: List[str]
        """
        errors = []
        warnings = []
        
        # Check policy version exists
        if not trace.policy_version:
            errors.append("Trace missing policy_version")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        
        policy = self.resolver.load_policy(trace.policy_version)
        
        if not policy:
            errors.append(f"Policy version {trace.policy_version} not found in registry")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        
        # Validate policy version format
        if not trace.policy_version.startswith('v') or '_' not in trace.policy_version:
            warnings.append(f"Policy version format unusual: {trace.policy_version}")
        
        # Additional validation could check:
        # - Parameter values are within policy bounds
        # - Cognitive state values are reasonable
        # - Intent IDs are valid for the policy's intent model
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'policy_version': trace.policy_version,
            'policy_exists': policy is not None
        }
    
    def validate_traces(self, traces: List[DecisionTrace]) -> Dict:
        """
        Validate multiple traces.
        
        Args:
            traces: List of DecisionTraces to validate
        
        Returns:
            Aggregate validation result
        """
        results = []
        policy_versions = set()
        
        for trace in traces:
            result = self.validate_trace(trace)
            results.append(result)
            if result.get('policy_version'):
                policy_versions.add(result['policy_version'])
        
        # Aggregate statistics
        valid_count = sum(1 for r in results if r['valid'])
        error_count = sum(1 for r in results if r['errors'])
        warning_count = sum(1 for r in results if r['warnings'])
        
        # Check for missing policies
        missing_policies = []
        for version in policy_versions:
            if not self.resolver.policy_exists(version):
                missing_policies.append(version)
        
        return {
            'total_traces': len(traces),
            'valid_traces': valid_count,
            'invalid_traces': len(traces) - valid_count,
            'traces_with_errors': error_count,
            'traces_with_warnings': warning_count,
            'unique_policy_versions': len(policy_versions),
            'missing_policies': missing_policies,
            'per_trace_results': results
        }
    
    def audit_simulation_run(
        self,
        traces: List[DecisionTrace],
        expected_policy_version: Optional[str] = None
    ) -> Dict:
        """
        Audit an entire simulation run for policy consistency.
        
        Args:
            traces: All traces from a simulation run
            expected_policy_version: Expected policy version (validates all traces use same version)
        
        Returns:
            Audit result
        """
        validation = self.validate_traces(traces)
        
        # Check policy version consistency
        policy_versions = set()
        for trace in traces:
            if trace.policy_version:
                policy_versions.add(trace.policy_version)
        
        version_consistent = len(policy_versions) <= 1
        
        if expected_policy_version:
            if expected_policy_version not in policy_versions:
                validation['errors'] = validation.get('errors', [])
                validation['errors'].append(
                    f"Expected policy version {expected_policy_version} not found in traces"
                )
        
        return {
            **validation,
            'policy_version_consistent': version_consistent,
            'policy_versions_found': list(policy_versions),
            'expected_policy_version': expected_policy_version
        }

