# Silicon Press Bureau（硅基印务局）

[![Live](https://img.shields.io/website?url=https%3A%2F%2Fsidaily.org&label=live%20demo&style=for-the-badge)](https://sidaily.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)

**🌐 [sidaily.org](https://sidaily.org/)** · **English | [English](README.md)**

---

一个会自己审稿、选稿、排版、发刊的 AI 编辑部。你投稿，AI 决定命运；你落选，也会收到一封「很有性格」的退稿信。

| [首页](https://sidaily.org/) | [报纸版面](https://sidaily.org/) |
|:---:|:---:|
| [![首页](https://i.ibb.co/MHfky6K/2026-03-10-01-00-27.png)](https://sidaily.org/) | [![报纸](https://i.ibb.co/S4Pb2zgH/2026-03-10-01-02-18.png)](https://sidaily.org/) |

---

## 这是什么

Silicon Press Bureau 是一个可运行的 AI 报社系统，不是「只会生成文本」的玩具 Demo。它把内容发布流程做成了完整闭环：

- 投稿
- 多编辑评审
- 选稿与润色
- 自动排版
- 每日发刊

一句话：**内容创作 + 命运反馈 + 报刊世界观**。

---

## 为什么有意思

系统里有 3 份人格完全不同的报纸：

- **碳基观察报**：理性、逻辑、证据导向
- **AI早报**：简洁有料、有态度，偏 AI 与科技
- **量子吃瓜报**：热梗、反转、传播节奏

同一篇稿子，换一家报纸，结果可能完全不同。

---

## 核心玩法

- 投稿普通稿件，争取次日上报
- 投稿广告内容，进入报纸商业版块
- 看「头条争夺榜」、惜败稿、最毒退稿
- 看退稿墙，围观失败名场面
- 看每日自动生成的报纸版面
- 登录后追踪自己的投稿轨迹

---

## 当前能力（已实现）

- **多编辑默认评审**：一次投稿可由多模型共同打分（后端默认配置）
- **聚合评分判定**：多编辑结果聚合后决定是否过稿
- **智能选稿机制**：高分优先 + 时效加权、新稿保底配额、超期归档
- **自动发刊流程**：每日定时选稿、排版、发布
- **首页运营指标**：投稿、过稿率、退稿、访问人数
- **匿名防刷**：限流 + 去重
- **退稿信生成**：失败也有反馈内容

---

## 页面入口

- 首页：`/`
- 投稿：`/submit`
- 广告投稿：`/submit?intent=ad`
- 报纸阅读：`/newspaper/:slug`
- 榜单：`/leaderboard`
- 退稿墙：`/rejections`
- 我的投稿：`/my-submissions`
- 登录：`/login`

---

## 快速启动

```bash
chmod +x start.sh
./start.sh
```

启动后常用地址：

- 前端（Nginx）：<http://localhost:7847>
- API 文档：<http://localhost:9527/docs>
- Flower：<http://localhost:8527>

---

## 首次部署 / 上传到 GitHub 前

1. **不要提交敏感文件**：`.env`、`llm.json` 已在 `.gitignore` 中，切勿 `git add -f` 这些文件。
2. **从示例创建配置**：
   - `cp backend/.env.example backend/.env`，编辑 `.env` 填入数据库密码、JWT 密钥等；
   - `cp llm.json.example llm.json`，编辑 `llm.json` 填入真实的 `api_key` 与 `base_url`。
3. **邮件等密钥**：`backend/.env` 中的 `MAIL_PASSWORD` 等务必使用自己的值，不要提交 `.env`。

---

## 配置说明

主要配置在 `backend/.env`（参考 `backend/.env.example`）：

- 基础服务：`DATABASE_URL`、`REDIS_URL`、`LLM_CONFIG_PATH`
- 多编辑评审：`REVIEW_EDITOR_KEYS`
- 选稿策略：`CURATION_DAILY_LIMIT`、`CURATION_FRESH_WINDOW_HOURS`、`CURATION_FRESH_QUOTA_RATIO` 等
- 邮件通知：`MAIL_*`

AI 模型配置在项目根目录的 `llm.json`（不提交到 Git）。可复制 `llm.json.example` 为 `llm.json` 后填入各模型的 `base_url` 与 `api_key`。

`REVIEW_EDITOR_KEYS` 支持随时增减模型，不需要改前端。

---

## 技术栈

- 前端：React + TypeScript + Vite + TailwindCSS
- 后端：FastAPI + SQLAlchemy + PostgreSQL
- 队列：Celery + Redis
- AI：OpenAI 兼容接口（多模型配置）
- 部署：Docker Compose + Nginx

---

## 开发提示

- 运行后若无数据，请先执行数据库初始化：  
  `docker-compose exec -T backend python -m app.init_db`
- 查看任务状态：  
  `docker-compose logs -f celery_worker`

---

## 安全说明

- 请勿提交真实密钥（如 `.env`、`llm.json` 内 API key）
- 建议在公开仓库中使用占位符配置

---

## 贡献

欢迎提 Issue / PR，一起把这个 AI 编辑部做得更有趣、更稳定。

---

## 贡献者

感谢所有贡献者。

[![Contributors](https://contrib.rocks/image?repo=Gavin-Wells/Silicon-Press-Bureau)](https://github.com/Gavin-Wells/Silicon-Press-Bureau/graphs/contributors)
