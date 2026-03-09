# Silicon Press Bureau

[![Live](https://img.shields.io/website?url=https%3A%2F%2Fsidaily.org&label=live%20demo&style=for-the-badge)](https://sidaily.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)

**🌐 [sidaily.org](https://sidaily.org/)** · **中文 | [简体中文](README.zh-CN.md)**

---

An AI editorial system that reviews, selects, lays out, and publishes. You submit; the AI decides. If you’re rejected, you still get a distinctive rejection letter.

| [Home](https://sidaily.org/) | [Newspaper](https://sidaily.org/) |
|:---:|:---:|
| [![Home](https://i.ibb.co/MHfky6K/2026-03-10-01-00-27.png)](https://sidaily.org/) | [![Newspaper](https://i.ibb.co/S4Pb2zgH/2026-03-10-01-02-18.png)](https://sidaily.org/) |

---

## What it is

Silicon Press Bureau is a runnable AI newspaper system—not a text-only demo. It closes the loop:

- Submissions
- Multi-editor (multi-model) review
- Curation and editing
- Auto layout
- Daily issues

**In short: content creation + fate feedback + newspaper world-building.**

---

## Why it’s interesting

Three newspapers with distinct personalities:

- **Carbon Observer** (理性、逻辑、证据) — rational, evidence-driven
- **AI Morning Post** — concise, opinionated, tech/AI focus
- **Quantum Tabloid** — memes, twists, virality

The same piece can get different outcomes at different papers.

---

## What you can do

- Submit articles and try to make the next day’s issue
- Submit ad content into business sections
- Browse the leaderboard (headlines, near-misses, harshest rejections)
- Browse the rejection wall
- Read daily auto-generated layouts
- Log in and track your submissions

---

## Features

- **Multi-editor review** — multiple models score each submission
- **Aggregate scoring** — combined result decides accept/reject
- **Curation** — freshness quota, time decay, archiving
- **Daily pipeline** — scheduled curation, layout, publish
- **Rejection letters** — generated per rejection
- **Anonymous + rate limiting** — anti-spam and dedup
- **Optional mail** — accept/reject notifications

---

## Quick start

```bash
chmod +x start.sh
./start.sh
```

Then:

- **Frontend (Nginx):** <http://localhost:7847>
- **API docs:** <http://localhost:9527/docs>
- **Flower:** <http://localhost:8527>

---

## First-time setup / Before pushing to GitHub

1. **Do not commit secrets.** `.env` and `llm.json` are in `.gitignore`; never `git add -f` them.
2. **Create config from examples:**
   - `cp backend/.env.example backend/.env` — set DB password, JWT secret, etc.
   - `cp llm.json.example llm.json` — set real `api_key` and `base_url` per model.
3. **Mail and other keys** — set `MAIL_PASSWORD` and the like in `backend/.env`; never commit `.env`.

---

## Configuration

Main config: `backend/.env` (see `backend/.env.example`).

- **Services:** `DATABASE_URL`, `REDIS_URL`, `LLM_CONFIG_PATH`
- **Review:** `REVIEW_EDITOR_KEYS`
- **Curation:** `CURATION_DAILY_LIMIT`, `CURATION_FRESH_WINDOW_HOURS`, `CURATION_FRESH_QUOTA_RATIO`, etc.
- **Mail:** `MAIL_*`

LLM config lives in project-root `llm.json` (not in Git). Copy `llm.json.example` to `llm.json` and fill in `base_url` and `api_key` for each model.

---

## Tech stack

- **Frontend:** React + TypeScript + Vite + TailwindCSS
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Queue:** Celery + Redis
- **AI:** OpenAI-compatible API (multi-model via `llm.json`)
- **Deploy:** Docker Compose + Nginx

---

## Dev tips

- **No data after start?** Run:  
  `docker-compose exec -T backend python -m app.init_db`
- **Watch tasks:**  
  `docker-compose logs -f celery_worker`

---

## Security

- Do not commit real keys (e.g. in `.env`, `llm.json`).
- Use placeholder config in public repos.

---

## Contributing

Issues and PRs welcome. Let’s make this AI newsroom more fun and robust.

---

## Contributors

Thanks to everyone who contributes.

[![Contributors](https://contrib.rocks/image?repo=Gavin-Wells/Silicon-Press-Bureau)](https://github.com/Gavin-Wells/Silicon-Press-Bureau/graphs/contributors)
