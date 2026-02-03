# Microsoft Agents Testing Framework — One‑Pager (SDK Leadership)

## Summary
The Microsoft Agents Testing Framework is an SDK-adjacent capability that makes M365 Agents testing in Python **reliable, repeatable, and scalable across repos** by standardizing the hardest parts of agent testing: **sending activities correctly, receiving responses reliably, and asserting on them ergonomically**.

It is intentionally designed as a **framework-agnostic testing harness** (Scenario → ClientFactory → AgentClient), with **pytest as an optional integration layer** for teams that want fixtures/markers.

Leadership outcome: higher-quality agents ship faster, with fewer regressions, and less duplicated test plumbing across the ecosystem.

## The Problem
Today, most Python agent tests either:
- don’t exist,
- are tightly coupled to a specific web host,
- re-implement brittle plumbing (auth tokens, callback servers, request shaping), or
- degrade into “string contains” checks on raw payloads.

The result is slow iteration, hard-to-debug failures, and inconsistent test quality across repos.

At scale, this becomes a product risk: regressions surface late, test patterns fragment across teams, and SDK changes are harder to validate with confidence.

## What This Framework Provides (Core Features)

### 1) A formal interaction API (`AgentClient`)
A single, consistent API for:
- sending activities/messages,
- collecting replies (including async callbacks),
- handling delivery modes (`expect_replies`, invoke), and
- capturing an auditable transcript for debugging.

This is the critical “bridge” between the developer’s intent and the SDK’s real runtime behavior.

### 2) Scenario-based testing (SDK-focused, host-agnostic)
Scenarios own lifecycle and infrastructure:
- **In-process scenarios** (today: `AiohttpScenario`) for fast integration testing and access to internals.
- **External scenarios** (`ExternalScenario`) for testing a running agent endpoint without re-writing callback plumbing.

This lets developers test **SDK behavior and agent logic** without locking the test model to any specific host framework.

### 3) Fluent selection + assertions (`Select`, `Expect`)
Agent responses are collections of models/activities, and real tests often need:
- “any response matches X”,
- “none match Y”,
- “exactly N match Z”,
- meaningful failure diagnostics.

The fluent layer provides quantifiers, filtering, and human-readable failure messages so tests stay concise and maintainable.

### 4) Transcript-first debugging and logging
The transcript model (`Transcript`/`Exchange`) captures request/response timing, status codes, and activities.
Logging/formatters make it easy to:
- print conversations at different detail levels,
- attach transcripts to CI logs, and
- debug intermittent/async issues without re-running locally.

### 5) Optional pytest ergonomics (plugin/fixtures)
The pytest plugin is a convenience layer:
- `@pytest.mark.agent_test(...)` supplies fixtures like `agent_client` and (for in-process) `agent_environment`.
- Teams that don’t use pytest can still use scenarios directly (`async with scenario.client()`).

## Non-goals
- Not a replacement for true E2E tests (deployment, infra, and environment validation still require E2E coverage).
- Not a new hosting framework for agents (it tests agents; it does not prescribe how agents are hosted).
- Not a general-purpose HTTP testing tool (the scope is agent activities, agent responses, and SDK-relevant flows).
- Not a guarantee of cross-channel behavioral parity (channel-specific differences still need targeted tests).
- Not a one-time implementation: it is expected to evolve alongside the SDK surface (e.g., streaming).

## Architecture (Why It’s Extendable)
The codebase is structured around stable seams:
- **Scenario contract**: `Scenario.run()` yields a **ClientFactory**.
- **AgentClient**: central interaction surface; should remain stable as capabilities expand (e.g., streaming).
- **Transport/hosting**: aiohttp implementation lives behind scenarios and sender/callback abstractions.
- **Assertions**: fluent engine is reusable anywhere you have lists of models/activities.

This separation makes it straightforward to add new scenarios (e.g., **FastAPI/ASGI**) without changing how tests are written.

## Addressing Common Critiques (and Why They Don’t Block Adoption)

### “It’s coupled to pytest.”
Not at the core.
- The *core* is Scenario/AgentClient and can be used from any async test runner or scripts.
- Pytest is an optional integration surface to reduce ceremony and improve discoverability.

### “It’s coupled to aiohttp.”
Partially, and intentionally localized.
- In-process hosting is aiohttp today because it’s lightweight and well-supported for async test servers.
- The design anticipates additional hosts (e.g., **FastAPIScenario/ASGI**) without changing tests.

### “These abstractions hide reality / reduce fidelity.”
They hide boilerplate, not behavior.
- Activities still flow through the SDK’s real adapter/authorization paths.
- Transcript capture increases observability vs ad-hoc tests.
- The framework supports both in-process and external endpoint scenarios to balance speed and realism.

### “This will replace E2E tests.”
It shouldn’t, and it doesn’t.
- Use **in-process** for fast integration coverage and SDK correctness.
- Use **external scenario** tests for endpoint-level checks.
- Keep a smaller set of true E2E tests for deployment/environment validation.

### “Maintenance burden / version drift with the SDK.”
This is exactly why a shared framework is needed.
- Centralizing the tricky pieces (auth, callback handling, activity shapes) reduces drift across repos.
- Tests in this repo act as a compatibility suite; changes are caught once, upstream.

### “Streaming isn’t supported yet.”
Correct, and the design is positioned for it.
- `AgentClient` is the right abstraction to add streaming APIs without forcing users to rewrite scenario setup or assertions.

## Roadmap (Near-Term)
- Add **FastAPI/ASGI scenario** to broaden hosting support.
- Add **streaming support** in `AgentClient`.
- Expand “sample scenarios” and recipes that focus on SDK behaviors (auth, invoke, async callbacks, state).

## Why This Matters for M365 Agents SDK for Python Developers
This framework fills a current gap: agent testing is either missing or inflexible.
By providing a reusable interaction layer + scenarios + fluent assertions + transcript debugging, it makes it practical for SDK users to:
- write tests earlier,
- write more meaningful assertions,
- debug failures faster, and
- keep tests consistent across projects.
