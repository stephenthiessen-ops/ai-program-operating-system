AI Program Operating System

A framework for AI-native program leadership inside modern engineering organizations.

This repository outlines a structured operating model that transforms raw execution data into strategic intelligence using automation, structured workflows, and AI augmentation.

The objective is simple:

Turn delivery systems into decision systems.

Core Components

• Structured program architecture
• Automated execution rollups
• AI-powered signal detection
• Delivery confidence modeling
• Executive-ready narrative generation

Philosophy

Traditional program management tracks work.
AI-native program leadership interprets work.

This OS is designed to reduce cognitive load, surface risk early, and convert operational telemetry into strategic clarity.

## Demo Output
- Latest executive brief: [`outputs/exec-brief_LATEST.md`](outputs/exec-brief_LATEST.md)

## How it works (high level)
1. Normalize execution data into a canonical schema
2. Derive deterministic signals (confidence, volatility, risk)
3. Generate a decision-oriented exec brief
4. Publish outputs back into the operating cadence
5. Repeat weekly via GitHub Actions

## Latest Outputs
- Executive brief: [`outputs/exec-brief_LATEST.md`](outputs/exec-brief_LATEST.md)
- Portfolio heatmap (CSV): [`outputs/portfolio_heatmap.csv`](outputs/portfolio_heatmap.csv)
- Heatmap summary: [`outputs/portfolio_heatmap_SUMMARY.md`](outputs/portfolio_heatmap_SUMMARY.md)

## Dashboard Demo
Run locally:
```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
