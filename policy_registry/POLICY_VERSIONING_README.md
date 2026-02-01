# Policy Versioning System

## Overview

The Policy Versioning System ensures that every DecisionTrace is linked to an immutable policy definition. This enables:

- **Interpretability**: Past decisions remain interpretable even when policies change
- **Auditability**: Every decision can be traced back to the policy that generated it
- **Replayability**: Decisions can be replayed under different policies (counterfactuals)
- **Consistency**: Trace-policy integrity is validated and enforced

## Core Concepts

### Policy Definition

A `PolicyDefinition` is an immutable snapshot of:
- Behavioral engine module and version
- Intent model module and version
- Parameter bounds and defaults
- Calibrated parameters (if any)
- Creation timestamp and metadata

### Policy Version

A policy version is a unique identifier (e.g., `v1_3f8a1b2c`) where:
- `v1` is the version number
- `3f8a1b2c` is a hash of the policy definition

The hash ensures that identical policies get the same version, even if created at different times.

### Policy Registry

The policy registry is an append-only store of policy definitions. Once a policy is saved, it is never modified. New policies are always added, never updated.

## Usage

### Creating a Policy Snapshot

```python
from policy_registry import create_policy_snapshot, PolicyResolver

# Create snapshot from current system state
policy = create_policy_snapshot(
    calibrated_parameters={'BASE_COMPLETION_RATE': 0.65},
    calibration_file='credigo_ss_calibration_summary.json',
    description='Credigo SS calibrated policy'
)

# Save to registry
resolver = PolicyResolver()
version = resolver.save_policy(policy)
print(f"Policy version: {version}")
```

### Getting Current Policy Version

```python
from policy_registry.get_current_policy import get_current_policy_version

# Get or create current policy version
version = get_current_policy_version(
    calibrated_parameters=calibrated_params,
    description='Current production policy'
)
```

### Loading a Policy

```python
from policy_registry import PolicyResolver

resolver = PolicyResolver()
policy = resolver.load_policy('v1_3f8a1b2c')

if policy:
    print(f"Engine: {policy.engine_module}")
    print(f"Created: {policy.created_at}")
    print(f"Parameters: {policy.parameter_bounds}")
```

### Validating Traces

```python
from policy_registry import PolicyAuditor
from decision_graph import DecisionTrace

auditor = PolicyAuditor()

# Validate single trace
result = auditor.validate_trace(trace)
if not result['valid']:
    print(f"Errors: {result['errors']}")

# Validate simulation run
audit_result = auditor.audit_simulation_run(traces, expected_policy_version='v1_3f8a1b2c')
print(f"Valid traces: {audit_result['valid_traces']}/{audit_result['total_traces']}")
```

## Integration with Decision Traces

Decision traces automatically get the current policy version when created:

```python
# In behavioral_engine_intent_aware.py
from policy_registry.get_current_policy import get_current_policy_version

current_policy_version = get_current_policy_version()

trace = create_decision_trace(
    ...,
    policy_version=current_policy_version
)
```

## Directory Structure

```
policy_registry/
├── policies/              # Policy definition files (append-only)
│   ├── v1_3f8a1b2c.json
│   ├── v2_7d9e4f5a.json
│   └── ...
├── policy_definition.py   # PolicyDefinition dataclass
├── policy_resolver.py     # Policy version resolution
├── policy_auditor.py      # Trace-policy validation
├── get_current_policy.py  # Get/create current policy version
└── __init__.py
```

## Key Principles

1. **Immutability**: Policies are never modified once saved
2. **Deterministic Hashing**: Identical policies get identical versions
3. **Append-Only**: New policies are added, never updated
4. **Trace Linkage**: Every trace must have a valid policy_version
5. **Validation**: Traces are validated against their policy versions

## Future Enhancements

- Git commit hash tracking for engine code
- Policy comparison utilities
- Policy migration tools
- Policy lineage tracking

