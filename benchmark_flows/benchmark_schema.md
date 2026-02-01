# Benchmark Flow Schema

## Structure

Each benchmark flow JSON file contains:

```json
{
  "product_name": "Zerodha",
  "category": "trading",
  "description": "India's largest discount broker",
  "steps": {
    "step_0": {
      "step_name": "Landing Page",
      "step_index": 0,
      "step_type": "landing",
      "effort_demand": 0.1,
      "risk_signal": 0.1,
      "explicit_value": 0.8,
      "reassurance_signal": 0.3,
      "cognitive_demand": 0.2,
      "intent_signals": {
        "trading": 0.9,
        "investment": 0.7
      },
      "description": "Value prop: low brokerage, start trading"
    },
    "step_1": {
      "step_name": "Email/Phone Entry",
      "step_index": 1,
      "step_type": "data_collection",
      "effort_demand": 0.2,
      "risk_signal": 0.1,
      "explicit_value": 0.3,
      "reassurance_signal": 0.2,
      "cognitive_demand": 0.1,
      "intent_signals": {
        "trading": 0.7,
        "investment": 0.7
      },
      "description": "Enter email or phone number"
    }
  }
}
```

## Force Value Ranges

- **effort_demand**: 0.0 (no effort) to 1.0 (very high effort)
- **risk_signal**: 0.0 (no risk) to 1.0 (high risk)
- **explicit_value**: 0.0 (no value shown) to 1.0 (clear value)
- **reassurance_signal**: 0.0 (no reassurance) to 1.0 (strong reassurance)
- **cognitive_demand**: 0.0 (no cognitive load) to 1.0 (high cognitive load)
- **intent_signals**: 0.0 (no alignment) to 1.0 (perfect alignment)

## Step Types

- **landing**: Landing page / value proposition
- **data_collection**: Asking for information
- **verification**: OTP, email verification
- **kyc**: Know Your Customer / identity verification
- **value_reveal**: First value moment
- **action**: User can perform primary action

## Design Principles

1. **Relative, not absolute**: Force values are relative to each other, not perfect replicas
2. **Heuristic but consistent**: Based on public knowledge and UX best practices
3. **Decision-focused**: Values chosen to reflect behavioral decision-making

