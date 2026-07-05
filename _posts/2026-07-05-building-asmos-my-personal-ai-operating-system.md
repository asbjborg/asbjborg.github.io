---
title: "Building ASMOS: My Personal AI Operating System"
date: 2026-07-05 18:00:00 +0200
last_modified_at: 2026-07-05 22:35:00 +0200
tags: [asmos, ai, pkm, cursor, agents, open-source]
---

For years my digital life looked like everyone else's: a folder called `code` with dozens of repos inside, a notes app here, a chat thread there, and an agent in Cursor that had amnesia every time I opened a different window.

That worked until it didn't. I wanted **one place** where my notes, my agent memory, my skills, and my projects could see each other — without turning everything into a monorepo.

So I built **ASMOS**.

## What ASMOS is

**ASM** (Asbjørn) + **OS** (operating system) = **ASMOS**.

One folder on disk. One Cursor window. Agents get the whole picture.

It is *not* a git monorepo. It is a **workspace OS**:

| Layer | Role |
| --- | --- |
| `AGENTS.md` | The manual — schema, workflows, agent rules |
| `wiki/` | A Karpathy-style personal knowledge wiki |
| `wiki/memories/` | Long-term agent memory with decay and forgetting |
| `.cursor/skills/` | Shared capabilities (`ingest`, `remember`, `curate`, …) |
| `repos/<name>/` | Nested code projects — each keeps its own git remote |
| `capture/` | Inbox for stuff waiting to be ingested into the wiki |

The outer repo tracks the OS itself. Code inside `repos/` pushes to GitHub independently, the way it always did — except now agents can read across repos without me juggling windows.

## The problem I was solving

Most "AI setups" are really **collections of freelancers**:

- ChatGPT doesn't know what Cursor did yesterday.
- Cursor doesn't know what's in my notes.
- Every repo is an island with its own rules, if any.

A real team shares context, vocabulary, history, and goals. I wanted infrastructure for *that* — a persistent layer above whichever model or vendor I rent this week.

> Own your context. Rent your intelligence.

ASMOS holds the memory. Models are interchangeable collaborators.

## Design influences

I stole shamelessly from people smarter than me:

- **[Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** — immutable `raw/` sources, distilled `wiki/` concepts
- **[Hermes Agent memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)** — bounded hot cache (`MEMORY.md`, `USER.md`), importance decay, archive instead of delete
- **[repo-of-repos](https://github.com/raffertyuy/repo-of-repos)** — read everywhere, write in one repo at a time
- **Nate Herk's AIS-OS** — one root folder, "other worlds" under `repos/`

The result feels less like a notes app and more like an operating system for agents.

## How I actually use it

### Capture → ingest

I dump quick notes, chat exports, and fragments into `capture/`. No frontmatter, no ceremony — presence in the folder means *pending*.

When I'm ready to process the inbox (and I treat that as a **ritual**, not a chore), I open ASMOS in Cursor and run `@ingest`. The agent:

1. Picks a home under `raw/<subfolder>/`
2. Writes or updates wiki concepts with links to the archived source
3. Moves the file out of `capture/` and stamps it as ingested

Empty inbox. Knowledge filed. I stay in the loop without babysitting YAML.

### Memory that forgets on purpose

Agents write atomic memories to `wiki/memories/active/` with importance scores. A scheduled script applies cognitive-style decay — old unused facts fade and eventually archive. Frequently accessed memories stay warm.

No review queue. No "please confirm you still want to remember this." The system drifts toward what I actually use.

### Nested repos, one window

I'm migrating projects from `~/Documents/code/` into `repos/` in batches. This blog lived in a weird nested folder (`asbjborg_site/asbjborg.github.io`) until today — now it's `repos/asbjborg.github.io/` inside ASMOS, still pushing to the same GitHub remote.

## Still early

ASMOS is a weekend's worth of architecture and a week's worth of migration — not a product launch. The wiki is sparse. Most of `~/Documents/code/` is still outside the OS.

But the loop works: capture, ingest, remember, code — all in one tree. Codex, Cursor, and ChatGPT can all read the same `USER.md` and `AGENTS.md` and actually know who they're talking to.

If you're building something similar, the repo is public: [github.com/asbjborg/asmos](https://github.com/asbjborg/asmos).

More posts as the migration continues. For now — this one is proof the nested-repo setup survives a real push. 🚀
