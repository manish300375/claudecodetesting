# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository structure

`claudetesting/` is a container for multiple independent projects (it sits in `claudecodeprojects/` alongside `claudetesting2/`). Each project folder is self-contained (own `.venv`, `.env`, `.gitignore`, `tools/`, `workflows/`, `.tmp/`, `output/`) and has its **own `CLAUDE.md`** with project-specific commands, decisions, and cost rules. Read that file first when working in a project. This root file holds the shared rules every project follows; project files must not repeat them.

There is no build, lint, or test setup at the root. Run a project's tools from inside its folder with its own venv (e.g. `cd <Project> && .venv/bin/python tools/<name>.py`); tool paths resolve relative to the project folder.

## WAT framework (Workflows, Agents, Tools)

Probabilistic AI handles reasoning; deterministic code handles execution. Offloading steps to scripts keeps accuracy high (five steps at 90% each is only ~59% overall).

- **Workflows**: markdown SOPs in `workflows/`. Each defines the objective, required inputs, tools to use, expected outputs, and edge cases.
- **Agent (you)**: read the relevant workflow, run tools in order, handle failures, ask clarifying questions. Don't do by hand what a tool does.
- **Tools**: Python scripts in `tools/` for API calls, transforms, file operations. Credentials come from the project's `.env`.

## How to operate

1. **Reuse first.** Check `tools/` before writing a new script.
2. **Learn from failures.** Read the full error, fix the tool, retest, then record the lesson in the workflow (rate limits, quirks, edge cases). Loop: identify → fix → verify → update workflow → move on.
3. **Workflows are protected.** Keep them current as you learn, but ask before creating or overwriting one unless told to explicitly.
4. **Paid calls.** If a tool uses paid APIs or credits, check with the user before re-running it after a failure, and show a cost estimate before any large spend.
5. **Secrets** live only in `.env` (with `.env.example` listing names). Never read or print `.env`.
6. **Deliverables vs intermediates.** Final outputs go to a cloud service the user can open (e.g. Google Drive) plus a local path in `output/`. `.tmp/` is disposable and regenerable.

## Standard project layout

```
<Project>/
  CLAUDE.md       # project-specific only; inherits this file
  workflows/      # SOPs
  tools/          # scripts
  .tmp/           # disposable intermediates (gitignored)
  output/         # final deliverables (gitignored)
  .env, .env.example, requirements.txt, .venv/
  credentials.json, token.json   # Google OAuth (gitignored)
```

## Adding a new project

1. Create the folder with the layout above and a `.gitignore` covering `.env`, `.venv/`, `.tmp/`, `output/`, `credentials.json`, `token.json`.
2. Create its `CLAUDE.md` from this template, filling only what is specific to the project:

```
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Inherits the WAT framework and shared guidelines from `../CLAUDE.md`.

## Project: <name>
<purpose; one-time or recurring>

## Commands
<setup, run tools, run a single step>

## Decisions already made
## Cost / rate-limit rules
## Inputs and outputs
```
