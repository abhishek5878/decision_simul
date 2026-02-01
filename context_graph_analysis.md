# Context Graph Analysis - Credigo Simulation

Generated from decision traces captured during simulation run.

## Graph Structure

- **Total Nodes**: 7,053
  - Persona nodes
  - Step nodes  
  - Intent nodes
  - Failure mode nodes

- **Total Edges**: 90,482
  - Decision edges (persona → step)
  - Alignment edges (step → intent)
  - Causal edges (step → failure mode)

## Key Insights

### 1. Dominant Failure Paths

The context graph reveals which steps cause the most rejections and why.

### 2. Persona-Step Rejection Patterns

Shows which persona types are systematically rejected at which steps.

### 3. Intent Alignment Impact

Analyzes how intent alignment scores correlate with continuation vs drop decisions.

### 4. Repeated Precedents

Identifies behavioral patterns that repeat across multiple personas.

## Usage

Run the analysis scripts to see:
- Step-level drop rates
- Dominant failure factors
- Intent alignment patterns
- Persona rejection maps

