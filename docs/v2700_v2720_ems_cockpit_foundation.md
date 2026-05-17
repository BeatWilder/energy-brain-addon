# V2700-V2720 EMS Cockpit Foundation

## Goal

Introduce explainable planner metadata
without changing controller safety behavior.

## Safety

- observer only
- no service calls
- no dispatch writes
- no AlphaESS control changes

## Adds

- planner explainability
- decision metadata
- constraint metadata
- dashboard badges
- future cockpit support structure

## Validation

Must prove:

- deterministic output
- reserve SOC constraints visible
- power clamp visibility
- no writes possible
