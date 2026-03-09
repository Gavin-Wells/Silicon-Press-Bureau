<div align="center">

# 📰 Silicon Press Bureau（硅基印务局）

**会自己审稿、选稿、排版、发刊的 AI 编辑部。你投稿，AI 定命运；被拒了，也能收到一封「有性格」的退稿信。**

[![在线试玩](https://img.shields.io/badge/🌐_在线试玩-sidaily.org-0ea5e9?style=for-the-badge)](https://sidaily.org/)
[![English](https://img.shields.io/badge/English-README.md-666?style=flat-square)](README.md)

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React%2018-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)

</div>

---

## ✨ 看看效果

| **首页** | **报纸版面** |
|:--------:|:-------------:|
| [<img src="https://i.ibb.co/MHfky6K/2026-03-10-01-00-27.png" width="400" alt="首页"/>](https://sidaily.org/) | [<img src="https://i.ibb.co/S4Pb2zgH/2026-03-10-01-02-18.png" width="400" alt="报纸"/>](https://sidaily.org/) |

👉 **[sidaily.org](https://sidaily.org/)** — 点开即玩。

---

## 🎯 这是什么？

一个**能跑起来的 AI 报社**，不是只会生成文字的玩具。完整链路：

- **投稿** → **多编辑（多模型）审稿** → **选稿与润色** → **自动排版** → **每日出刊**

一句话：**内容创作 + 命运反馈 + 报纸世界观**。

---

## 🗞️ 三份报纸，三种人格

| 报纸 | 调性 |
|------|------|
| **碳基观察报** | 理性、证据优先、观点锋利 |
| **AI早报** | 简洁有料、有态度、偏科技与 AI |
| **量子吃瓜报** | 热梗、反转、传播感强 |

同一篇稿子，投不同报纸 → 三种不同命运。玩的就是这个。

---

## 🧾 你可以做什么

- 投稿文章，冲击次日头版  
- 投广告内容，进入商业版块  
- 看**榜单**：头条、惜败稿、最毒退稿  
- 逛**退稿墙**  
- 读每日自动生成的报纸版面  
- 登录后追踪自己的投稿记录  

---

## ⚡ 功能一览

| | |
|---|---|
| 🤖 **多编辑审稿** | 多模型对每篇投稿打分 |
| 📊 **聚合评分** | 综合结果决定过稿 / 退稿 |
| 📅 **选稿机制** | 新稿配额、时效衰减、超期归档 |
| 🕐 **每日流水线** | 定时选稿 → 排版 → 发布 |
| ✉️ **退稿信** | 每封退稿都有生成内容 |
| 🛡️ **防刷** | 匿名限流 + 去重 |
| 📧 **可选邮件** | 过稿 / 退稿通知 |

---

## 🚀 快速启动

**一条命令**（Docker + Compose）：

```bash
chmod +x start.sh && ./start.sh
```

然后打开：

- **前端：** [http://localhost:7847](http://localhost:7847)
- **API 文档：** [http://localhost:9527/docs](http://localhost:9527/docs)
- **Flower：** [http://localhost:8527](http://localhost:8527)

没有数据？执行一次：

```bash
docker-compose exec -T backend python -m app.init_db
```

---

## ⚙️ 配置（首次部署 / 上传 GitHub 前）

1. **不要提交敏感文件。** `.env` 和 `llm.json` 已进 `.gitignore`，别用 `git add -f` 强制加入。
2. **从示例复制再改：**
   - `cp backend/.env.example backend/.env` — 填数据库密码、JWT 密钥等；
   - `cp llm.json.example llm.json` — 填各模型的真实 `api_key` 和 `base_url`。
3. **邮件等：** 在 `backend/.env` 里设 `MAIL_PASSWORD` 等，不要提交 `.env`。

**配置位置：** 主配置在 `backend/.env`（服务、审稿、选稿、邮件）；根目录 `llm.json` 管模型（不进 Git，用 `llm.json.example` 当模板）。

---

## 📦 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18、TypeScript、Vite、TailwindCSS |
| 后端 | FastAPI、SQLAlchemy、PostgreSQL |
| 队列 | Celery、Redis |
| AI | OpenAI 兼容接口（多模型，`llm.json` 配置） |
| 部署 | Docker Compose、Nginx |

---

## 🤝 参与贡献

欢迎 Issue 和 PR，一起把这个编辑部做得更有趣、更稳。

---

## 💜 贡献者

感谢每一位贡献者。

[![Contributors](https://contrib.rocks/image?repo=Gavin-Wells/Silicon-Press-Bureau)](https://github.com/Gavin-Wells/Silicon-Press-Bureau/graphs/contributors)
