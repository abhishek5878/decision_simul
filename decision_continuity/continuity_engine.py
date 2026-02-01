"""
ContinuityEngine - Orchestrates Decision Continuity & Precedent System

The ContinuityEngine is the main interface for:
- Recording DecisionEvents during simulation
- Maintaining ContinuityState per entity
- Building and querying PrecedentGraph
- Integrating with existing DecisionTrace, ContextGraph, DecisionAutopsy
"""

import json
from typing import Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime

from .decision_event import DecisionEvent, DecisionEventType, BeliefState, create_decision_event_from_trace
from .continuity_state import ContinuityState, EntityType
from .precedent_graph import PrecedentGraph


class ContinuityEngine:
    """
    ContinuityEngine - Main orchestrator for decision continuity system.
    
    This engine:
    - Captures DecisionEvents DURING execution
    - Maintains persistent ContinuityState per entity
    - Builds PrecedentGraph from historical events
    - Provides query interface for precedents
    - Integrates with existing DropSim components
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize ContinuityEngine.
        
        Args:
            storage_path: Optional path to persist state (JSON files)
        """
        self.storage_path = Path(storage_path) if storage_path else None
        
        # In-memory state
        self.continuity_states: Dict[str, ContinuityState] = {}  # entity_id -> ContinuityState
        self.precedent_graph = PrecedentGraph()
        self.event_history: List[DecisionEvent] = []  # Append-only event log
        
        # Load persisted state if available
        if self.storage_path and self.storage_path.exists():
            self._load_state()
    
    def record_event(
        self,
        event: DecisionEvent,
        update_continuity: bool = True,
        update_precedents: bool = True
    ):
        """
        Record a DecisionEvent during simulation execution.
        
        This is the primary method for capturing decisions DURING execution.
        
        Args:
            event: DecisionEvent to record
            update_continuity: Whether to update ContinuityState
            update_precedents: Whether to update PrecedentGraph
        """
        # Append to event history (immutable log)
        self.event_history.append(event)
        
        # Update continuity state
        if update_continuity:
            entity_key = f"{event.entity_type}:{event.entity_id}"
            if entity_key not in self.continuity_states:
                self.continuity_states[entity_key] = ContinuityState(
                    entity_id=event.entity_id,
                    entity_type=EntityType(event.entity_type)
                )
            
            continuity_state = self.continuity_states[entity_key]
            continuity_state.update_from_event(event)
        
        # Update precedent graph
        if update_precedents:
            # Find previous event in sequence
            previous_event = None
            if event.parent_event_id:
                previous_event = next(
                    (e for e in self.event_history if e.event_id == event.parent_event_id),
                    None
                )
            
            self.precedent_graph.add_event(event, previous_event)
        
        # Persist if storage path is set
        if self.storage_path:
            self._save_state()
    
    def record_event_from_trace(
        self,
        trace: 'DecisionTrace',  # Forward reference
        entity_id: str,
        entity_type: str,
        action_considered: str,
        action_taken: str,
        alternatives_rejected: List[str],
        outcome_observed: Optional[str] = None,
        confidence_level: float = 0.5,
        context: Optional[Dict] = None
    ) -> DecisionEvent:
        """
        Record a DecisionEvent from an existing DecisionTrace.
        
        This bridges the existing DecisionTrace system with DecisionEvent system.
        
        Returns:
            Created DecisionEvent
        """
        event = create_decision_event_from_trace(
            trace, entity_id, entity_type, action_considered, action_taken,
            alternatives_rejected, outcome_observed, confidence_level, context
        )
        
        self.record_event(event)
        return event
    
    def get_continuity_state(self, entity_id: str, entity_type: str) -> Optional[ContinuityState]:
        """Get ContinuityState for an entity."""
        entity_key = f"{entity_type}:{entity_id}"
        return self.continuity_states.get(entity_key)
    
    def get_or_create_continuity_state(self, entity_id: str, entity_type: str) -> ContinuityState:
        """Get or create ContinuityState for an entity."""
        entity_key = f"{entity_type}:{entity_id}"
        if entity_key not in self.continuity_states:
            self.continuity_states[entity_key] = ContinuityState(
                entity_id=entity_id,
                entity_type=EntityType(entity_type)
            )
        return self.continuity_states[entity_key]
    
    def query_precedents(
        self,
        step_id: str,
        trust: float,
        value: float,
        commitment: float,
        risk: float,
        intent: float,
        factors: Set[str],
        action: Optional[str] = None
    ) -> List[Dict]:
        """
        Query precedents matching given conditions.
        
        Returns what has worked in similar situations historically.
        """
        return self.precedent_graph.query_precedents(
            step_id, trust, value, commitment, risk, intent, factors, action
        )
    
    def query_what_usually_works(
        self,
        condition_description: str,
        step_id: Optional[str] = None
    ) -> List[Dict]:
        """
        High-level query: "What usually works when [condition]?"
        
        Example: "What usually works when belief collapses due to delayed value?"
        """
        return self.precedent_graph.query_what_usually_works(condition_description, step_id)
    
    def get_entity_belief_state(self, entity_id: str, entity_type: str) -> Dict[str, float]:
        """Get current belief state for an entity."""
        continuity_state = self.get_continuity_state(entity_id, entity_type)
        if continuity_state:
            return continuity_state.get_current_belief_state()
        return {
            'trust': 0.5,
            'value': 0.0,
            'commitment': 0.0
        }
    
    def has_irreversible_event(self, entity_id: str, entity_type: str, event_type: str) -> bool:
        """Check if entity has experienced an irreversible event."""
        continuity_state = self.get_continuity_state(entity_id, entity_type)
        if continuity_state:
            return continuity_state.has_irreversible_event(event_type)
        return False
    
    def _save_state(self):
        """Save state to disk."""
        if not self.storage_path:
            return
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Save continuity states
        continuity_file = self.storage_path / "continuity_states.json"
        continuity_data = {
            key: state.to_dict()
            for key, state in self.continuity_states.items()
        }
        with open(continuity_file, 'w') as f:
            json.dump(continuity_data, f, indent=2)
        
        # Save precedent graph
        precedent_file = self.storage_path / "precedent_graph.json"
        with open(precedent_file, 'w') as f:
            json.dump(self.precedent_graph.to_dict(), f, indent=2)
        
        # Save event history (last N events to avoid huge files)
        event_file = self.storage_path / "event_history.json"
        recent_events = self.event_history[-10000:]  # Last 10k events
        event_data = [e.to_dict() for e in recent_events]
        with open(event_file, 'w') as f:
            json.dump(event_data, f, indent=2)
    
    def _load_state(self):
        """Load state from disk."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        # Load continuity states
        continuity_file = self.storage_path / "continuity_states.json"
        if continuity_file.exists():
            with open(continuity_file, 'r') as f:
                continuity_data = json.load(f)
                self.continuity_states = {
                    key: ContinuityState.from_dict(data)
                    for key, data in continuity_data.items()
                }
        
        # Load precedent graph
        precedent_file = self.storage_path / "precedent_graph.json"
        if precedent_file.exists():
            with open(precedent_file, 'r') as f:
                precedent_data = json.load(f)
                self.precedent_graph = PrecedentGraph.from_dict(precedent_data)
        
        # Load event history
        event_file = self.storage_path / "event_history.json"
        if event_file.exists():
            with open(event_file, 'r') as f:
                event_data = json.load(f)
                self.event_history = [
                    DecisionEvent.from_dict(e) for e in event_data
                ]
    
    def export_summary(self) -> Dict:
        """Export summary of current state."""
        return {
            'total_entities': len(self.continuity_states),
            'total_events': len(self.event_history),
            'precedent_graph': {
                'total_nodes': len(self.precedent_graph.nodes),
                'total_edges': len(self.precedent_graph.edges),
                'total_events_processed': self.precedent_graph.total_events_processed
            },
            'entity_types': {
                entity_type.value: sum(
                    1 for state in self.continuity_states.values()
                    if state.entity_type == entity_type
                )
                for entity_type in EntityType
            }
        }

