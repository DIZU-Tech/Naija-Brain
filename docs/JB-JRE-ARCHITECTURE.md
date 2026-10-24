# Naija Brain — JB v0.9 + JRE Research Architecture

Naija Brain is the experimental proving ground for the core intelligence architecture planned for Jarvis 2.0. The implementation uses the same architectural responsibilities and flow, not a verbatim copy of the separate Jarvis repository.

## Jarvis Brain (JB)

The current JarvisBrain orchestrator runs:

1. **Receive** — bound and normalise the incoming message.
2. **Understand** — classify the intent, question type, English/Pidgin cues, and broad topic.
3. **Build context** — load recent turns, a session profile, and the last topic from first-party SQLite storage.
4. **Think / plan** — choose dialogue, clarification, profile memory, local time, calculation, knowledge retrieval, age reasoning, follow-up resolution, or an honest capability boundary.
5. **Delegate** — call the relevant local tool or JRE.
6. **Persist / evaluate** — save the turn, feedback, and a compact experiment event.

## Jarvis Response Engine (JRE)

JarvisResponseEngine runs the selected plan, retrieves local evidence when appropriate, applies deterministic reasoning, composes an English or Nigerian Pidgin response, validates the response, and returns confidence heuristics, local source identifiers, latency, and a trace.

The response trace is intentionally inspectable. Confidence is a heuristic—not a calibrated probability. model_used is false because this build invokes no neural language model.

## Independence boundary

- No external LLM API.
- No external search API.
- No hosted database for chat, memory, retrieval, or experiment logging.
- The knowledge corpus is local code/data and must be updated deliberately.
- Supabase is reserved for email/password and Google authentication in the later frontend phase; it is not the brain or application database.
- No Supabase project or credentials were changed in this commit.

## Storage and deployment

Chat sessions, turns, profile memory, feedback, and experiment events are stored in SQLite. On a normal self-hosted server, set NAIJA_BRAIN_DB_PATH to a durable path. On Vercel, this build uses /tmp/naija_brain.sqlite3; Vercel serverless local storage is ephemeral, so cross-instance durable memory is **not** guaranteed there. Durable storage without a third-party database requires a self-hosted persistent disk or a first-party database service.

## API

GET /api/chat returns health metadata. POST /api/chat accepts {"session": "id", "message": "text"} and returns reply, intent, qtype, lang, answered_by, confidence, sources, model_used, latency_ms, and trace.

## Honest limitations

This is a deterministic research prototype, not a trained general-purpose LLM. Its current knowledge is finite, its Pidgin and reference resolution are early implementations, and it cannot verify live facts while external retrieval is disabled. Unknown or current questions should trigger uncertainty rather than fabricated answers.
