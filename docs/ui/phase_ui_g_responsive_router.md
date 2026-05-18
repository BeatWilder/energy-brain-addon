# Phase UI-G — Responsive Auto Switching

## Goal

Automatic renderer switching:
- desktop
- tablet
- mobile

without cluttering runtime UI.

## Features

- automatic breakpoint detection
- manual override support
- config-driven behavior
- renderer-safe routing

## Breakpoints

- mobile: <700px
- tablet: 700-1399px
- desktop: >=1400px

## Safety

Renderer-only phase:
- no HA writes
- no controller impact
- no runtime dispatch
