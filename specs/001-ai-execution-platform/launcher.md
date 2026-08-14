# Launcher Design — AI Execution Platform (001)

## Goal
Best-effort detection and startup for uploaded application ZIPs so Playwright can run against a live target app.

## Responsibilities
- Inspect extracted source tree.
- Detect likely stack and startup command.
- Launch subprocess.
- Wait for readiness.
- Persist logs, port, and diagnostics.
- Support manual override when automatic detection is uncertain.

## Detection Heuristics
- `package.json` with scripts for Node-based apps.
- `requirements.txt`, `pyproject.toml`, or framework entrypoints for Python apps.
- Static HTML entrypoints.
- Known framework markers such as Vite, Next, React, Streamlit, Flask, FastAPI.

## Required Outputs
- detected stack
- startup command
- working directory
- environment variables
- chosen port
- readiness URL
- readiness result
- launcher logs
- manual override used flag

## Failure Rules
- Never fake a running app.
- Surface ambiguous detection as a clear operator choice.
- Preserve safety checks before execution even after successful launch.
