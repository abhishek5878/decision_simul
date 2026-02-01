#!/usr/bin/env python3
"""
dropsim_api.py - DropSim JSON API

Lightweight, local-only JSON API for DropSim.
No auth (dev-mode only).
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import json

from fintech_presets import get_default_fintech_scenario, compile_persona_from_raw
from fintech_demo import run_fintech_demo_simulation
from behavioral_engine import STATE_VARIANTS
from behavioral_aggregator import generate_full_report

app = FastAPI(
    title="DropSim API",
    description="Behavioral Simulation Engine API",
    version="1.0.0"
)


# ============================================================================
# Pydantic Models (Matching Design Doc Schema)
# ============================================================================

class PersonaRaw(BaseModel):
    """Raw persona fields."""
    SEC: float = Field(..., ge=0.0, le=1.0)
    UrbanRuralTier: float = Field(..., ge=0.0, le=1.0)
    DigitalLiteracy: float = Field(..., ge=0.0, le=1.0)
    FamilyInfluence: float = Field(..., ge=0.0, le=1.0)
    AspirationalLevel: float = Field(..., ge=0.0, le=1.0)
    PriceSensitivity: float = Field(..., ge=0.0, le=1.0)
    RegionalCulture: float = Field(..., ge=0.0, le=1.0)
    InfluencerTrust: float = Field(..., ge=0.0, le=1.0)
    ProfessionalSector: float = Field(..., ge=0.0, le=1.0)
    EnglishProficiency: float = Field(..., ge=0.0, le=1.0)
    HobbyDiversity: float = Field(..., ge=0.0, le=1.0)
    CareerAmbition: float = Field(..., ge=0.0, le=1.0)
    AgeBucket: float = Field(..., ge=0.0, le=1.0)
    GenderMarital: float = Field(..., ge=0.0, le=1.0)


class PersonaPriors(BaseModel):
    """Compiled behavioral priors."""
    CC: float = Field(..., ge=0.2, le=0.9)
    FR: float = Field(..., ge=0.1, le=0.8)
    RT: float = Field(..., ge=0.1, le=0.9)
    LAM: float = Field(..., ge=1.0, le=2.5)
    ET: float = Field(..., ge=0.2, le=0.9)
    TB: float = Field(..., ge=0.2, le=0.9)
    DR: float = Field(..., ge=0.05, le=0.9)
    CN: float = Field(..., ge=0.2, le=0.9)
    MS: float = Field(..., ge=0.3, le=1.0)


class Persona(BaseModel):
    """Persona with raw fields and optional compiled priors."""
    name: str
    description: str
    raw_fields: PersonaRaw
    compiled_priors: Optional[PersonaPriors] = None


class ProductStep(BaseModel):
    """Product step definition."""
    name: str
    description: Optional[str] = None
    cognitive_demand: float = Field(..., ge=0.0, le=1.0)
    effort_demand: float = Field(..., ge=0.0, le=1.0)
    risk_signal: float = Field(..., ge=0.0, le=1.0)
    irreversibility: int = Field(..., ge=0, le=1)
    delay_to_value: int = Field(..., ge=0, le=5)
    explicit_value: float = Field(..., ge=0.0, le=1.0)
    reassurance_signal: float = Field(..., ge=0.0, le=1.0)
    authority_signal: float = Field(..., ge=0.0, le=1.0)


class ScenarioConfig(BaseModel):
    """Complete scenario configuration."""
    scenario_name: Optional[str] = None
    personas: List[Persona]
    steps: List[ProductStep]
    state_variants: Optional[Dict] = None


class StepSummary(BaseModel):
    """Step-level summary."""
    step_name: str
    failure_rate: float
    primary_cost: Optional[str] = None
    primary_cost_pct: float = 0.0
    secondary_cost: Optional[str] = None
    secondary_cost_pct: float = 0.0
    total_trajectories: int
    failures: int


class PersonaSummary(BaseModel):
    """Persona-level summary."""
    persona_name: str
    dominant_exit_step: str
    dominant_failure_reason: Optional[str] = None
    consistency_score: float
    variants_completed: int
    variants_total: int


class ScenarioSummary(BaseModel):
    """Complete scenario summary."""
    scenario_name: str
    total_trajectories: int
    completed_trajectories: int
    completion_rate: float
    step_summaries: List[StepSummary]
    persona_summaries: List[PersonaSummary]


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/simulate", response_model=Dict)
async def simulate(
    scenario: ScenarioConfig,
    include_traces: bool = Query(False, description="Include full traces in response")
):
    """
    Run behavioral simulation for a scenario.
    
    Returns:
    - scenario_summary: Step-level and persona-level summaries
    - traces (optional): Full trajectory traces if include_traces=true
    """
    try:
        # Convert Pydantic models to dicts for engine
        personas_list = []
        for persona in scenario.personas:
            # Compile priors if not provided
            if persona.compiled_priors:
                priors = persona.compiled_priors.dict()
            else:
                priors = compile_persona_from_raw(persona.raw_fields.dict())
            
            personas_list.append({
                'name': persona.name,
                'description': persona.description,
                'raw_fields': persona.raw_fields.dict(),
                'priors': priors
            })
        
        # Convert steps to dict
        product_steps = {}
        for step in scenario.steps:
            product_steps[step.name] = {
                'cognitive_demand': step.cognitive_demand,
                'effort_demand': step.effort_demand,
                'risk_signal': step.risk_signal,
                'irreversibility': step.irreversibility,
                'delay_to_value': step.delay_to_value,
                'explicit_value': step.explicit_value,
                'reassurance_signal': step.reassurance_signal,
                'authority_signal': step.authority_signal,
                'description': step.description or step.name
            }
        
        # Use provided state variants or default
        state_variants = scenario.state_variants if scenario.state_variants else STATE_VARIANTS
        
        # Run simulation
        result_df = run_fintech_demo_simulation(
            personas_list,
            state_variants,
            product_steps,
            verbose=False
        )
        
        # Generate summary
        report = generate_full_report(result_df, product_steps=product_steps)
        
        # Build step summaries
        step_summaries = []
        total_trajectories = len(personas_list) * len(state_variants)
        
        for step_name in product_steps.keys():
            # Count failures at this step
            failures = 0
            failure_reasons = {}
            
            for _, row in result_df.iterrows():
                trajectories = row.get('trajectories', [])
                for traj in trajectories:
                    if traj.get('exit_step') == step_name:
                        failures += 1
                        reason = traj.get('failure_reason')
                        if reason:
                            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            
            failure_rate = failures / total_trajectories if total_trajectories > 0 else 0.0
            
            # Primary/secondary costs
            primary_cost = None
            primary_pct = 0.0
            secondary_cost = None
            secondary_pct = 0.0
            
            if failure_reasons:
                sorted_reasons = sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)
                if sorted_reasons:
                    primary_cost, primary_count = sorted_reasons[0]
                    primary_pct = (primary_count / failures * 100) if failures > 0 else 0.0
                    
                    if len(sorted_reasons) > 1:
                        secondary_cost, secondary_count = sorted_reasons[1]
                        secondary_pct = (secondary_count / failures * 100) if failures > 0 else 0.0
            
            step_summaries.append(StepSummary(
                step_name=step_name,
                failure_rate=failure_rate,
                primary_cost=primary_cost,
                primary_cost_pct=primary_pct,
                secondary_cost=secondary_cost,
                secondary_cost_pct=secondary_pct,
                total_trajectories=total_trajectories,
                failures=failures
            ))
        
        # Build persona summaries
        persona_summaries = []
        for _, row in result_df.iterrows():
            persona_summaries.append(PersonaSummary(
                persona_name=str(row['persona_name']).split('\n')[0],
                dominant_exit_step=row['dominant_exit_step'],
                dominant_failure_reason=row.get('dominant_failure_reason'),
                consistency_score=row['consistency_score'],
                variants_completed=row['variants_completed'],
                variants_total=row['variants_total']
            ))
        
        # Count completions
        completed = sum(p.variants_completed for p in persona_summaries)
        
        response = {
            "scenario_summary": {
                "scenario_name": scenario.scenario_name or "custom_scenario",
                "total_trajectories": total_trajectories,
                "completed_trajectories": completed,
                "completion_rate": completed / total_trajectories if total_trajectories > 0 else 0.0,
                "step_summaries": [s.dict() for s in step_summaries],
                "persona_summaries": [p.dict() for p in persona_summaries]
            }
        }
        
        # Add traces if requested
        if include_traces:
            traces = []
            for _, row in result_df.iterrows():
                for traj in row.get('trajectories', []):
                    traces.append({
                        "persona_name": str(row['persona_name']).split('\n')[0],
                        "variant": traj.get('variant'),
                        "exit_step": traj.get('exit_step'),
                        "failure_reason": traj.get('failure_reason'),
                        "journey": traj.get('journey', [])
                    })
            response["traces"] = traces
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "dropsim"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

