# Phase UI-B - Renderer Routing Layer

## Goal

Separate:
- runtime data
- presentation layer

## Supported renderers

### Desktop
Mission control layout.

### Tablet
Control panel layout.

### Mobile
Operator companion layout.

## Safety

This phase:
- does NOT modify runtime logic
- does NOT modify planner logic
- does NOT modify controller logic
- only routes presentation

Observer-safe.
