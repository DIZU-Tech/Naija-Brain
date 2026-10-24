# Naija Brain — JB/JRE Research Build

Naija Brain is the research project for the core intelligence architecture planned for Jarvis 2.0. The chat API now routes through modular responsibilities implemented in the Jarvis Brain (JB) and Jarvis Response Engine (JRE) research core.

## Current architecture
- **JB:** receive, understand, build context, plan, choose a local capability, and persist the outcome.
- **JRE:** local evidence retrieval, deterministic reasoning, English/Pidgin response composition, validation, trace and evaluation metadata.
- **Local tools:** safe arithmetic, Nigeria time, date-of-birth age calculations.
- **First-party storage:** SQLite session turns, profile memory, feedback, and experiment events.
- **No external LLM, web search, or hosted database is used to generate answers.**
- **Supabase is reserved for email/password and Google authentication in the later frontend phase only.**

## Run
Python 3.10+ is required. Core runtime uses Python's standard library.

```sh
python -m unittest discover -s tests -v
python server.py
```

The chat endpoint accepts POST /api/chat with JSON such as:
```json
{"session":"demo-session","message":"How old is Remi Tinubu?"}
```

Response metadata includes the reply, detected intent and language, answer path, confidence heuristic, local source identifiers, latency, and an inspectable pipeline trace.

## Boundaries
This is a deterministic research prototype, not a trained general-purpose LLM. The knowledge corpus is finite and has no live web access by design. Unsupported and current-data questions should be acknowledged instead of fabricated.

SQLite is durable on a normal self-hosted server with a persistent disk. On Vercel, /tmp is ephemeral, so persistent cross-instance memory is not guaranteed. See docs/JB-JRE-ARCHITECTURE.md.
