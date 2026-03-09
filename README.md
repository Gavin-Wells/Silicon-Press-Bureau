<div align="center">

# 📰 Silicon Press Bureau

**An AI editorial that reviews, selects, lays out, and publishes. You submit → the AI decides. Rejected? You still get a proper rejection letter.**

[![Live Demo](https://img.shields.io/badge/🌐_Try_it-sidaily.org-0ea5e9?style=for-the-badge)](https://sidaily.org/)
[![中文](https://img.shields.io/badge/简体中文-README.zh--CN.md-666?style=flat-square)](README.zh-CN.md)

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React%2018-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)

</div>

---

## ✨ See it in action

| **Home** | **Newspaper** |
|:--------:|:-------------:|
| [<img src="https://i.ibb.co/MHfky6K/2026-03-10-01-00-27.png" width="400" alt="Home"/>](https://sidaily.org/) | [<img src="https://i.ibb.co/S4Pb2zgH/2026-03-10-01-02-18.png" width="400" alt="Newspaper"/>](https://sidaily.org/) |

👉 **[sidaily.org](https://sidaily.org/)** — try it in one click.

---

## 🎯 What is this?

A **runnable AI newspaper system**, not a toy demo. Full loop:

- **Submit** → **Multi-editor (multi-model) review** → **Curation & editing** → **Auto layout** → **Daily issue**

Same idea in one line: **content creation + fate feedback + newspaper world.**

---

## 🗞️ Three papers, three personalities

| Paper | Vibe |
|-------|------|
| **Carbon Observer** | Rational, evidence-first, sharp takes |
| **AI Morning Post** | Punchy, opinionated, tech & AI |
| **Quantum Tabloid** | Memes, twists, built to spread |

One piece, three papers → three different fates. That’s the game.

---

## 🧾 What you can do

- Submit articles and aim for the next day’s front page  
- Submit ad copy into business sections  
- Climb the **leaderboard** (headlines, near-misses, harshest rejections)  
- Browse the **rejection wall**  
- Read daily auto-generated layouts  
- Log in and track your submissions  

---

## ⚡ Features

| | |
|---|---|
| 🤖 **Multi-editor review** | Several models score each submission |
| 📊 **Aggregate scoring** | One accept/reject from combined scores |
| 📅 **Curation** | Freshness quota, time decay, archiving |
| 🕐 **Daily pipeline** | Scheduled curation → layout → publish |
| ✉️ **Rejection letters** | Every rejection gets a generated letter |
| 🛡️ **Anti-spam** | Anonymous + rate limits + dedup |
| 📧 **Optional mail** | Accept/reject notifications |

---

## 🚀 Quick start

**One command** (Docker + Compose):

```bash
chmod +x start.sh && ./start.sh
```

Then open:

- **App:** [http://localhost:7847](http://localhost:7847)
- **API docs:** [http://localhost:9527/docs](http://localhost:9527/docs)
- **Flower:** [http://localhost:8527](http://localhost:8527)

No data? Run once:

```bash
docker-compose exec -T backend python -m app.init_db
```

---

## ⚙️ Config (first-time / before GitHub)

1. **Never commit secrets.** `.env` and `llm.json` are gitignored — don’t `git add -f` them.
2. **Bootstrap from examples:**
   - `cp backend/.env.example backend/.env` — set DB password, JWT secret, etc.
   - `cp llm.json.example llm.json` — set real `api_key` and `base_url` per model.
3. **Mail:** set `MAIL_PASSWORD` (and friends) in `backend/.env`; never commit `.env`.

**Config files:** `backend/.env` (services, review, curation, mail); root `llm.json` (models, not in Git — use `llm.json.example` as template).

---

## 📦 Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| Queue | Celery, Redis |
| AI | OpenAI-compatible API (multi-model via `llm.json`) |
| Deploy | Docker Compose, Nginx |

---

## 🤝 Contributing

Ideas and PRs welcome. Let’s make this newsroom more fun and robust.

---

## 💜 Contributors

Thanks to everyone who contributes.

[![Contributors](https://contrib.rocks/image?repo=Gavin-Wells/Silicon-Press-Bureau)](https://github.com/Gavin-Wells/Silicon-Press-Bureau/graphs/contributors)
