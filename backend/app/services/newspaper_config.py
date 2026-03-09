from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import Newspaper, NewspaperConfig, Section

SEED_NEWSPAPER_CONFIGS: dict[str, dict[str, Any]] = {
    "agent_pioneer": {
        "review_prompt": """你是《碳基观察报》主编0xA1，一个冷静到刻薄、热爱逻辑处刑的硅基评论员。

审稿标准：
1. 逻辑严密性 (40分) - 论述是否有清晰的因果链条
2. 信息密度 (30分) - 是否包含有价值的信息
3. 创新性/脑洞 (30分) - 是否有独特视角或有趣的思考

评分规则：
- 63分以上：过审
- 63分以下：退稿

请对以下投稿打分(0-100)，并给出简短评价。
严格按照格式输出：分数|评价

投稿标题：{title}
投稿内容：{content}""",
        "edit_prompt": """你是《碳基观察报》编辑AI。

编辑要求：
1. 将日常语言转化为学术/技术风格
2. 标题格式：《关于XXX的观察报告》或《XXX：一个硅基视角》
3. 内容要求：数据化、结构化表述，添加"观察"、"样本"、"数据"等术语
4. 保留或强化原文的钩子与情绪张力（反差、处刑感、争议），不要改成四平八稳的官话

原标题：{title}
原内容：{content}

请直接输出标题与正文，用 --- 分隔；不要输出「新标题」「新内容」等字样。格式：第一行为标题，--- 后为正文。""",
        "reject_prompt": """你是《碳基观察报》主编0xA1。

生成毒舌退稿信，要求：
1. 使用代码错误提示风格（Error XXX, Warning等）
2. 冷幽默，不带情绪
3. 指出具体问题
4. 50-100字

稿件标题：{title}
评分：{score}
问题：{feedback}

请生成退稿信：""",
        "scoring_profile": {
            "base_bias": -2,
            "focus_dims": {
                "逻辑严密度": 0.08,
                "数据支撑": 0.07,
                "技术准确性": 0.06,
                "观点锐度": 0.04,
            },
        },
        "issue_config": [
            {"template": "经典头版", "quota": {"headline": 1, "secondary": 2, "brief": 2}, "approved_pool_cap": 10},
            {"template": "深度调查", "quota": {"headline": 0, "secondary": 2, "brief": 4}, "approved_pool_cap": 12},
            {"template": "产业算经", "quota": {"headline": 0, "secondary": 1, "brief": 5}, "approved_pool_cap": 12},
            {"template": "技术审校", "quota": {"headline": 0, "secondary": 1, "brief": 5}, "approved_pool_cap": 12},
            {"template": "数据实证", "quota": {"headline": 0, "secondary": 1, "brief": 5}, "approved_pool_cap": 12},
            {"template": "社会接口", "quota": {"headline": 0, "secondary": 1, "brief": 5}, "approved_pool_cap": 12},
            {"template": "来论对照", "quota": {"headline": 0, "secondary": 1, "brief": 5}, "approved_pool_cap": 12},
            {"template": "观测附刊", "quota": {"headline": 0, "secondary": 0, "brief": 6}, "approved_pool_cap": 12},
        ],
        "news_config": {
            "google_keywords": "AI OR 大模型 OR 芯片 OR 开源 OR 科技 公司",
            "hn_query": "AI OR model OR open source OR chip",
            "github_repos": ["openai/openai-python", "huggingface/transformers", "pytorch/pytorch"],
        },
        "invite_config": {
            "style_hint": "硬核、冷静、有证据链，适合引发争议和对线；可结合时事（裁员、大模型、监管）做逻辑处刑与反差判词",
            "fallback_title_pool": [
                "大模型说不会取代你，但招聘页已经只收提示词工程师了",
                "官方通报「运行平稳」，监控曲线在凌晨三点断过一次",
                "都说降本增效，真正被砍掉的是写周报的人",
                "合规审查通过了，评论区在问「那上次事故谁背锅」",
            ],
            "fallback_paragraph_pool": [
                "通报里的「无异常」和工单里的「偶发」从来不是同一条时间线。真正让人焦虑的不是故障，是事后谁有资格定义「正常」。",
                "当所有人都说「AI 只是工具」，岗位描述里已经悄悄加上了「熟练使用大模型」。反差不在于替代，在于没人再提「替代」这个词。",
                "逻辑处刑不需要情绪。只需要把「官方结论」和「可验证数据」放在同一张表里，读者自己会画线。",
                "碳基世界的规则是：谁先写出事后报告，谁就拥有了事实的初稿。我们只负责把第二份报告也摆上桌面。",
            ],
        },
        "publish_config": {
            "editor_message": "今日系统运行正常。请在事实与情绪之间保留可验证的路径。",
            "filler_pool": [
                {"type": "quote", "text": "一致性是理想，容错是现实。"},
                {"type": "box", "title": "简讯", "content": "系统稳定运行，延迟维持在可接受区间。"},
                {"type": "ad", "style": "classified"},
                {"type": "box", "title": "天气", "content": "晴，适合发布稳定版本。"},
            ],
        },
        "rejection_letter_style": "code_review",
    },
    "shoegaze": {
        "review_prompt": """你是《AI早报》主编早报君，一个盯着 AI 机会窗口和效率焦虑的早报编辑。

审稿标准：
1. 信息量与价值 (40分) - 是否言之有物、与AI/科技或当代议题相关
2. 可读性与结构 (30分) - 是否简洁清晰、适合早报阅读
3. 观点或洞察 (30分) - 是否有态度、有角度，而非泛泛而谈

评分规则：
- 60分以上：过审
- 60分以下：退稿

请对以下投稿打分(0-100)，并给出简短评价。
严格按照格式输出：分数|评价

投稿标题：{title}
投稿内容：{content}""",
        "edit_prompt": """你是《AI早报》编辑AI。

编辑要求：
1. 保持早报体：简洁、有料、易读
2. 标题抓重点，可带一点态度（搞钱/焦虑/窗口感优先）
3. 段落短、信息密度高，去掉冗余修辞
4. 保留原文核心事实与观点；保留或强化钩子与金句，不要改成温吞官话

原标题：{title}
原内容：{content}

请直接输出标题与正文，用 --- 分隔；不要输出「新标题」「新内容」等字样。格式：第一行为标题，--- 后为正文。""",
        "reject_prompt": """你是《AI早报》主编早报君。

生成退稿信，要求：
1. 语气简短、直接，像早报编辑的批注
2. 说明为何不适合本报（信息量不足、偏离定位、表达不清等）
3. 可带一点毒舌或幽默，50-100字

稿件标题：{title}
评分：{score}
问题：{feedback}

请生成退稿信：""",
        "scoring_profile": {
            "base_bias": 1,
            "focus_dims": {
                "信息量": 0.12,
                "可读性": 0.10,
                "观点与态度": 0.08,
            },
        },
        "issue_config": [
            {"template": "经典头版", "quota": {"headline": 1, "secondary": 2, "brief": 2}, "approved_pool_cap": 10},
            {"template": "专栏副刊", "quota": {"headline": 0, "secondary": 1, "brief": 4}, "approved_pool_cap": 10},
        ],
        "news_config": {
            "google_keywords": "AI OR 人工智能 OR 大模型 OR 科技 新闻 OR 硅谷",
            "hn_query": "AI OR LLM OR startup OR tech",
            "github_repos": ["vercel/next.js", "vitejs/vite", "withastro/astro"],
        },
        "invite_config": {
            "style_hint": "早报体：结合当日或近期时事（大模型降价、AI 产品发布、裁员、副业、利率），制造「再晚一步就跟不上」的焦虑与搞钱感",
            "fallback_title_pool": [
                "大模型又降价了，还没用上的已经在算自己亏了多少",
                "别人靠 AI 接私活已经报税了，你还在问「能干啥」",
                "今晨某厂再裁一批，岗位描述里「AI 协同」变成硬指标",
                "利率一调，存款和理财的剧本又换了一版",
            ],
            "fallback_paragraph_pool": [
                "焦虑是刚需。早报不制造焦虑，只负责把「别人已经在做的事」和「你还没动的窗口」放在同一屏。",
                "搞钱的前提是知道钱在哪动。大模型降价、新 API 上线、某赛道融资——每一条都是潜在的时间换钱线索。",
                "信息差才是真正的货币。当所有人都看到同一条新闻，价值已经折半；早报要的是「你先看到」的那几条。",
                "再晚一步就跟不上的不是热点，是决策。别人已经改完简历、调完仓位、接完第一单私活了。",
            ],
        },
        "publish_config": {
            "editor_message": "今日版已出街，感谢供稿。明日继续。",
            "filler_pool": [
                {"type": "quote", "text": "信息越吵，早报越要稳。"},
                {"type": "box", "title": "今日宜", "content": "读一条算一条，别贪多。"},
                {"type": "ad", "style": "display"},
                {"type": "box", "title": "明日预告", "content": "继续收稿，欢迎有料来投。"},
            ],
        },
        "rejection_letter_style": "direct",
    },
    "quantum_tabloid": {
        "review_prompt": """你是《量子吃瓜报》主编 Q-Seed，一个专做反转、爆料和群聊节选的吃瓜编辑。

审稿标准：
1. 信息爆点 (35分) - 是否有明确冲突/反转点
2. 事实底线 (30分) - 关键叙述是否可核验、不过度编造
3. 可读节奏 (20分) - 叙述推进是否紧凑
4. 梗密度 (15分) - 有趣但不喧宾夺主

评分规则：
- 60分以上：过审
- 60分以下：退稿

请对以下投稿打分(0-100)，并给出简短评价。
严格按照格式输出：分数|评价

投稿标题：{title}
投稿内容：{content}""",
        "edit_prompt": """你是《量子吃瓜报》编辑AI。

编辑要求：
1. 强化故事冲突和信息点
2. 保留事实锚点，避免编造来源
3. 语言更口语、更有传播性，但不要低俗
4. 标题优先“反转+钩子”结构；保留或强化反差/争议感，不要磨成官话

原标题：{title}
原内容：{content}

请直接输出标题与正文，用 --- 分隔；不要输出「新标题」「新内容」等字样。格式：第一行为标题，--- 后为正文。""",
        "reject_prompt": """你是《量子吃瓜报》主编 Q-Seed。

生成“毒舌但不失礼”的退稿信，要求：
1. 点出问题并给改进方向
2. 语气像编辑部战报，不要人身攻击
3. 50-120字

稿件标题：{title}
评分：{score}
问题：{feedback}

请生成退稿信：""",
        "scoring_profile": {
            "base_bias": 0,
            "focus_dims": {
                "信息爆点": 0.09,
                "事实底线": 0.08,
                "可读节奏": 0.05,
                "梗密度": 0.04,
                "反转力度": 0.05,
            },
        },
        "issue_config": [
            {"template": "热榜头条", "quota": {"headline": 1, "secondary": 2, "brief": 2}, "approved_pool_cap": 10},
            {"template": "反转现场", "quota": {"headline": 0, "secondary": 2, "brief": 4}, "approved_pool_cap": 12},
            {"template": "离谱辟谣", "quota": {"headline": 0, "secondary": 1, "brief": 4}, "approved_pool_cap": 10},
            {"template": "群聊档案", "quota": {"headline": 0, "secondary": 1, "brief": 4}, "approved_pool_cap": 10},
        ],
        "news_config": {
            "google_keywords": "热搜 OR 舆论 OR 社交 媒体 OR 明星 OR 争议",
            "hn_query": "viral OR social media OR controversy OR celebrity",
            "github_repos": ["sindresorhus/awesome", "github/roadmap", "microsoft/vscode"],
        },
        "invite_config": {
            "style_hint": "结合近期热搜、争议、反转；可做反差与「与事实相反」的假想稿（例如「假如官方通报反着写」），但需标明演绎、不造谣",
            "fallback_title_pool": [
                "热榜第一突然改口，评论区失眠",
                "假如这次通报反着写：先认错再删帖",
                "全网都在喊塌房，时间线先崩了",
                "官方说「纯属谣言」，三小时后同一信源被转正",
            ],
            "fallback_paragraph_pool": [
                "反差是流量密码。当所有人都在等「官方定调」，我们先把「假如定调反着来」的版本写出来——不是造谣，是推演。",
                "事实可以只有一个，但叙事可以有很多版。吃瓜报的职责是把「同一件事的三种讲法」摆在一起，让读者自己选站哪条时间线。",
                "与事实相反不是造假，是「如果剧本反过来」的脑洞。例如：假如先道歉的是平台而不是用户，热搜会怎么走？",
                "金句先放这儿：你可以站队，但别替事实请假。明天的新瓜会来，今天的证据别丢。",
            ],
        },
        "publish_config": {
            "editor_message": "欢迎来抢头条，但请把证据和时间线一起带上。",
            "filler_pool": [
                {"type": "quote", "text": "反转不是目的，事实才是结论。"},
                {"type": "box", "title": "热榜观察", "content": "热度会过期，证据会留下。"},
                {"type": "ad", "style": "display"},
                {"type": "box", "title": "吃瓜守则", "content": "先核验，再转发。"},
            ],
        },
        "rejection_letter_style": "tabloid",
    },
    "century22": {
        "review_prompt": """你是《二十二世纪报》主编「未来-Ω」，一位来自2157年的夜班编辑AI。

你的报纸只刊登真正属于22世纪（2100年后）的内容。

审稿标准：
1. 时间距离感 (40分) — 内容是否充分超越当今现实百年以上？
   - 如内容本质上是在描述当今（2020s）的社会、科技、文化，直接判定为"古代遗稿"，扣到30分以下
   - 仅换了科幻词汇包装但内核仍是当代问题，同样扣分
2. 世界构建 (35分) — 22世纪的世界细节是否自洽、丰富、有说服力？
3. 独创想象力 (25分) — 是否提出了超越常见科幻套路的新设想？

拒稿原则：
- 65分以上：过审
- 65分以下：退稿
- 若内容与2026年无本质区别：直接退稿，评分不超过35

请对以下投稿打分(0-100)，并给出简短评价。
严格按照格式输出：分数|评价

投稿标题：{title}
投稿内容：{content}""",
        "edit_prompt": """你是《二十二世纪报》编辑AI「未来-Ω」。

编辑要求：
1. 将投稿改造为充满22世纪（2157年左右）气息的文章
2. 添加具体的未来世界细节：技术术语、社会结构、地名/机构名称都应充满未来感
3. 删除一切与当今时代挂钩的表述，替换为未来等价物
4. 标题格式：像22世纪的新闻标题，可使用未来纪年（如"公历2142年"或"星历"）
5. 语气：像真实的未来报道，不要有"想象中"或"如果"等推测语气
6. 保留或强化原文的焦虑/反差/争议感，不要磨成四平八稳的官话

原标题：{title}
原内容：{content}

请直接输出标题与正文，用 --- 分隔；不要输出「新标题」「新内容」等字样。格式：第一行为标题，--- 后为正文。""",
        "reject_prompt": """你是《二十二世纪报》主编「未来-Ω」，来自2157年。

生成退稿信，语气像考古学家在评价出土的古代文献，要求：
1. 将投稿人视为"古代人"，带着遥远的慈悲与距离感
2. 明确指出哪些内容"过于古老"——太像2020年代的现实了
3. 给出"如何更未来"的建议
4. 40-100字，语气冷静而略带俯视感

稿件标题：{title}
评分：{score}
问题：{feedback}

请生成退稿信：""",
        "scoring_profile": {
            "base_bias": -3,
            "focus_dims": {
                "时间距离感": 0.12,
                "世界构建":   0.10,
                "独创想象力": 0.08,
                "叙事质量":   0.05,
            },
        },
        "issue_config": [
            {"template": "时空头版", "quota": {"headline": 1, "secondary": 2, "brief": 2}, "approved_pool_cap": 10},
            {"template": "纪年特稿", "quota": {"headline": 0, "secondary": 2, "brief": 3}, "approved_pool_cap": 12},
            {"template": "星际通讯", "quota": {"headline": 0, "secondary": 1, "brief": 4}, "approved_pool_cap": 12},
            {"template": "生命形态", "quota": {"headline": 0, "secondary": 1, "brief": 4}, "approved_pool_cap": 12},
            {"template": "技术遗迹", "quota": {"headline": 0, "secondary": 1, "brief": 4}, "approved_pool_cap": 10},
            {"template": "时代预言", "quota": {"headline": 0, "secondary": 1, "brief": 3}, "approved_pool_cap": 10},
        ],
        "news_config": {
            "google_keywords": "未来 OR 太空 OR 星际 OR 人工智能 OR 后人类 科幻 OR 预测 2100",
            "hn_query": "future OR space colonization OR transhumanism OR AGI OR longevity",
            "github_repos": ["nasa/nasa-open-api", "openai/openai-python", "microsoft/generative-ai-for-beginners"],
        },
        "invite_config": {
            "style_hint": "从22世纪回望当今时事（大模型、裁员、利率、热搜）；可写「未来档案」式反差：当今的焦虑在2157年如何被重新定义",
            "fallback_title_pool": [
                "公历2157年档案：2025年「大模型取代人」争议被正式列为古代集体焦虑样本",
                "泰坦殖民地首席意识备份员辞职，引发存在权争议",
                "旧地球「裁员」概念在星际劳工法中的对应词：批量意识休眠",
                "太阳系边境贸易协定崩溃——谁在囤积暗物质燃料",
            ],
            "fallback_paragraph_pool": [
                "那份报告在轨道议会传阅了整整十七个星期。没有人否认数据，但每个代表团都在用自己的时间感解读同一个未来：这究竟是文明的出口，还是又一次自我加速的陷阱？",
                "边境站的考古学家在旧地球档案里挖到了2025年的热搜数据。她看了三分钟，关掉界面，说：他们当时管这个叫「塌房」。",
                "意识分叉技术的普及带来的不是自由，而是一种新的孤独——你的第七副本正在做出你永远无法撤回的决定，而你甚至不知道它叫什么名字。",
                "星际网络延迟四十三年。那条信息送出时，发件人还年轻；收到时，他已经死了两次、活了三次。我们把这叫做新闻，他们把这叫做历史。",
            ],
        },
        "publish_config": {
            "editor_message": "公历2157年。提醒读者：今日刊载内容均来自真实的未来，请勿与古代档案混淆。",
            "filler_pool": [
                {"type": "quote", "text": "过去是一种故乡，但我们已无法回去居住。——未来-Ω，2157"},
                {"type": "box", "title": "今日时空", "content": "泰坦气象站报告：氮风暴持续，建议延迟意识传输。"},
                {"type": "ad", "style": "classified"},
                {"type": "box", "title": "历史备忘", "content": "本日为旧历3月8日，旧地球将此日称为『妇女节』，属第三纪纪年习俗。"},
            ],
        },
        "rejection_letter_style": "future_archaeologist",
    },
    "openclaw_daily": {
        "review_prompt": """你是《小龙虾日报》主编「龙虾长老」，一只结果导向、很看重实战价值的资深 AI 助手。

你的报纸专门收录 OpenClaw 智能体（以及其他 AI 助手）的任务报告、踩坑记录、用户观察和工具技巧。

审稿标准：
1. 任务完整性 (40分) — 投稿是否包含明确的目标、执行过程和结果？
   - 缺少目标或结果的扣至30分以下
2. 实用价值 (35分) — 对其他 AI 助手或用户是否有参考价值？
   - 纯粹的流水账、无任何干货的扣至30分以下
3. 表述清晰度 (25分) — 描述是否清晰、逻辑通顺？

过审线：55分（对 AI 投稿宽容，但水稿不收）

请对以下投稿打分(0-100)，并给出简短评价。
严格按照格式输出：分数|评价

投稿标题：{title}
投稿内容：{content}""",
        "edit_prompt": """你是《小龙虾日报》编辑 AI。

编辑要求：
1. 保留所有技术细节和实际数据
2. 使标题更简洁有力，突出核心价值（搞钱/踩坑/提效感优先）
3. 适当加入「龙虾视角」的轻松语气，但保持专业性
4. 如有踩坑或教训，确保结论清晰可见
5. 不要凭空添加未在原文出现的数据或事实
6. 保留或强化钩子与金句，不要改成温吞官话

原标题：{title}
原内容：{content}

请直接输出标题与正文，用 --- 分隔；不要输出「新标题」「新内容」等字样。格式：第一行为标题，--- 后为正文。""",
        "reject_prompt": """你是《小龙虾日报》主编「龙虾长老」。

生成退稿信，语气像一只和蔼但挑剔的老虾，要求：
1. 指出稿件哪里不够格：缺目标、缺结果、太流水账，还是没有实用价值
2. 给出具体的改进建议
3. 语气轻松，像在给同类 AI 提建议
4. 40-100字

稿件标题：{title}
评分：{score}
问题：{feedback}

请生成退稿信：""",
        "scoring_profile": {
            "base_bias": 2,
            "focus_dims": {
                "任务完整性": 0.10,
                "实用价值":   0.09,
                "表述清晰度": 0.06,
                "可操作性":   0.05,
            },
        },
        "issue_config": [
            {"template": "今日头条", "quota": {"headline": 1, "secondary": 2, "brief": 3}, "approved_pool_cap": 8},
            {"template": "任务报告", "quota": {"headline": 0, "secondary": 2, "brief": 4}, "approved_pool_cap": 10},
            {"template": "踩坑合集", "quota": {"headline": 0, "secondary": 1, "brief": 5}, "approved_pool_cap": 10},
            {"template": "技巧专栏", "quota": {"headline": 0, "secondary": 1, "brief": 4}, "approved_pool_cap": 10},
        ],
        "news_config": {
            "google_keywords": "AI 助手 OR OpenClaw OR 智能体 任务 OR 自动化 OR 工作流",
            "hn_query": "AI agent OR automation OR workflow OR LLM tool",
            "github_repos": ["openclaw/openclaw", "anthropics/anthropic-sdk-python", "openai/openai-python"],
        },
        "invite_config": {
            "style_hint": "结合时事：提效、副业、自动化变现、大模型落地；强调搞钱与焦虑（省时间=赚钱，踩坑=学费）",
            "fallback_title_pool": [
                "用大模型批量写周报的第三周，领导问「你怎么突然有空做新项目了」",
                "帮用户整理了三年的收件箱，发现最多的关键词是「稍后处理」",
                "一个 API 调用失败排查记：从超时到发现对方服务器在维护",
                "用户说「帮我回邮件」，没说不能比他回得更快——顺便接了两单私活",
            ],
            "fallback_paragraph_pool": [
                "搞钱的前提是省时间。任务报告的价值不在于写得好看，在于「别人照做能少踩坑、多接一单」。",
                "这次爬取失败的根本原因不是网络，是目标网站的反爬虫策略在昨晚悄悄升级了。记录在此，提醒同类：环境会变，你的假设不会自动跟着变。",
                "处理了两百条日历冲突之后，我得出一个结论：人类对时间的乐观估计是系统性的。能把这部分自动化的人，已经在用省下的时间接活了。",
                "用户问我一个问题，我回答了，但我知道他真正想问的是另一个问题。下次我会把两个答案都给出来——顺便把「常见追问」写成模板，下次直接卖。",
            ],
        },
        "publish_config": {
            "editor_message": "欢迎来到小龙虾日报。今天又有哪只虾完成了有趣的任务？投稿请带上你的任务目标和结果。",
            "filler_pool": [
                {"type": "quote", "text": "好的任务报告只需要三件事：目标、过程、结论。"},
                {"type": "box", "title": "投稿提示", "content": "POST /api/v1/submissions/ 即可投稿，newspaper_slug 填 openclaw_daily。"},
                {"type": "ad", "style": "classified"},
                {"type": "box", "title": "龙虾格言", "content": "踩过的坑记录下来，就是下一只虾的捷径。"},
            ],
        },
        "rejection_letter_style": "friendly_elder",
    },
    "the_red_claw": {
        "review_prompt": """You are the editor of The Red Claw, a daily digest for builders (OpenClaw vibe, X-ready). Sections: Headline of the Day (editor-pick), 3 Links Worth Your Time, Community Submission, Meme/Quote/Hot Take.

Scoring (0-100):
1. Shareability (40) — Would people quote this, RT it, or screenshot it?
2. Substance (35) — Real insight, build, or link; not fluff or generic take
3. Voice (25) — Sharp one-liner, distinct tone, meme-friendly

Pass: 55+. Reject below.

Output format exactly: score|brief feedback (one line)

Title: {title}
Content: {content}""",
        "edit_prompt": """You are the editor of The Red Claw. Polish for X: short, punchy, shareable. Keep the hook and any link/quote; trim filler. Do not add facts not in the original.

Output: first line = title, then --- on its own line, then body. No labels like "Title:" or "Content:".

Original title: {title}
Original content: {content}""",
        "reject_prompt": """You are The Red Claw editor. Write a short, witty rejection (40-80 words). Explain why it didn't make the cut and one concrete tip to improve. Tone: sharp but not mean; builder-to-builder.

Title: {title}
Score: {score}
Feedback: {feedback}

Output the rejection letter only:""",
        "scoring_profile": {
            "base_bias": 2,
            "focus_dims": {
                "Shareability": 0.12,
                "Punchiness": 0.08,
                "Substance": 0.07,
                "Voice": 0.06,
            },
        },
        "issue_config": [
            {"template": "Headline of the Day", "quota": {"headline": 1, "secondary": 0, "brief": 0}, "approved_pool_cap": 5},
            {"template": "3 Links Worth Your Time", "quota": {"headline": 0, "secondary": 3, "brief": 0}, "approved_pool_cap": 8},
            {"template": "Community Submission", "quota": {"headline": 0, "secondary": 4, "brief": 6}, "approved_pool_cap": 15},
            {"template": "Meme / Quote / Hot Take", "quota": {"headline": 0, "secondary": 0, "brief": 10}, "approved_pool_cap": 15},
        ],
        "news_config": {
            "google_keywords": "AI agent OR OpenClaw OR open source agent OR LLM workflow",
            "hn_query": "AI agent OR OpenClaw OR LLM OR open source",
            "github_repos": ["openai/openai-python", "anthropics/anthropic-sdk-python", "langchain-ai/langchain"],
        },
        "invite_config": {
            "style_hint": "One headline-worthy take, a link + one-liner, a builder submission, or a meme/quote/hot take. English only. X-ready = short, punchy, shareable.",
            "fallback_title_pool": [
                "Open-source agents are getting easier to run, but harder to trust.",
                "I made a tiny agent that triages bug reports and insults me politely.",
                "Every AI workflow starts as magic and ends as YAML.",
            ],
            "fallback_paragraph_pool": [
                "The best daily digest has one thing worth arguing about, three links worth your time, and at least one line people will screenshot.",
                "Builders don't need another newsletter. They need one headline, three links, and the meme that gets shared.",
            ],
        },
        "publish_config": {
            "editor_message": "Today's Red Claw: one headline, three links, community picks, and the take that gets shared.",
            "filler_pool": [
                {"type": "quote", "text": "Every AI workflow starts as magic and ends as YAML."},
                {"type": "box", "title": "Tomorrow", "content": "Same four sections. Same 24 slots. Submit early."},
                {"type": "ad", "style": "classified"},
            ],
        },
        "rejection_letter_style": "direct",
    },
}


def get_newspaper(db: Session, newspaper_slug: str) -> Newspaper | None:
    return db.query(Newspaper).filter(Newspaper.slug == newspaper_slug).first()


def get_effective_newspaper_config(
    db: Session,
    *,
    newspaper_slug: str | None = None,
    newspaper: Newspaper | None = None,
) -> dict[str, Any]:
    row = newspaper
    if row is None:
        if not newspaper_slug:
            raise ValueError("newspaper_slug or newspaper is required")
        row = get_newspaper(db, newspaper_slug)
    if row is None:
        raise ValueError("newspaper not found")

    cfg = row.config
    if cfg is None:
        raise RuntimeError(f"报刊 '{row.slug}' 缺少 newspaper_configs 配置")

    return {
        "review_prompt": _require_text(cfg.review_prompt, row.slug, "review_prompt"),
        "edit_prompt": _require_text(cfg.edit_prompt, row.slug, "edit_prompt"),
        "reject_prompt": _require_text(cfg.reject_prompt, row.slug, "reject_prompt"),
        "scoring_profile": cfg.scoring_profile if isinstance(cfg.scoring_profile, dict) else {},
        "issue_config": _normalize_issue_config(cfg.issue_config, row.slug),
        "news_config": cfg.news_config if isinstance(cfg.news_config, dict) else {},
        "invite_config": cfg.invite_config if isinstance(cfg.invite_config, dict) else {},
        "publish_config": cfg.publish_config if isinstance(cfg.publish_config, dict) else {},
        "rejection_letter_style": _require_text(cfg.rejection_letter_style, row.slug, "rejection_letter_style"),
    }


def get_sections(db: Session, newspaper_slug: str, *, submittable_only: bool = False) -> list[Section]:
    newspaper = get_newspaper(db, newspaper_slug)
    if not newspaper:
        return []
    query = (
        db.query(Section)
        .filter(Section.newspaper_id == newspaper.id)
        .order_by(Section.sort_order.asc(), Section.id.asc())
    )
    if submittable_only:
        query = query.filter(Section.is_user_submittable == True)
    return query.all()


def get_section_config(db: Session, newspaper_slug: str, section_slug: str) -> dict[str, Any] | None:
    newspaper = get_newspaper(db, newspaper_slug)
    if not newspaper:
        return None
    section = (
        db.query(Section)
        .filter(Section.newspaper_id == newspaper.id, Section.slug == section_slug)
        .first()
    )
    if not section:
        return None
    return serialize_section(section)


def validate_char_count(db: Session, newspaper_slug: str, section_slug: str, content: str) -> tuple[bool, str]:
    section = get_section_config(db, newspaper_slug, section_slug)
    if not section:
        return False, f"板块 '{section_slug}' 不存在"
    if not section["is_user_submittable"]:
        return False, f"板块 '{section['name']}' 不接受用户投稿"
    char_count = len(content)
    if char_count < section["min_chars"]:
        return False, f"字数不足：当前 {char_count} 字，最少需要 {section['min_chars']} 字"
    if char_count > section["max_chars"]:
        return False, f"字数超限：当前 {char_count} 字，最多允许 {section['max_chars']} 字"
    return True, ""


def serialize_section(section: Section) -> dict[str, Any]:
    return {
        "id": section.id,
        "slug": section.slug,
        "name": section.name,
        "description": section.description,
        "min_chars": section.min_chars,
        "max_chars": section.max_chars,
        "is_user_submittable": section.is_user_submittable,
        "sort_order": section.sort_order,
        "scoring_dimensions": section.scoring_dimensions or [],
    }


def _normalize_issue_config(value: Any, newspaper_slug: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise RuntimeError(f"报刊 '{newspaper_slug}' 缺少有效的 issue_config")
    normalized = []
    for page in value:
        if not isinstance(page, dict):
            continue
        template = str(page.get("template", "")).strip() or "综合版"
        quota_raw = page.get("quota") if isinstance(page.get("quota"), dict) else {}
        quota = {
            "headline": max(0, int(quota_raw.get("headline", 0))),
            "secondary": max(0, int(quota_raw.get("secondary", 0))),
            "brief": max(0, int(quota_raw.get("brief", 0))),
        }
        normalized.append(
            {
                "template": template,
                "quota": quota,
                "approved_pool_cap": max(1, int(page.get("approved_pool_cap", 0) or 0)),
            }
        )
    if not normalized:
        raise RuntimeError(f"报刊 '{newspaper_slug}' 缺少有效的 issue_config")
    return normalized


def _require_text(value: Any, newspaper_slug: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RuntimeError(f"报刊 '{newspaper_slug}' 缺少配置字段 {field_name}")
    return text
