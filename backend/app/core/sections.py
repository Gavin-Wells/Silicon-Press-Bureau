"""
板块定义注册表 (Section Registry)

每份报纸的板块配置：名称、字数范围、评分维度权重。
该模块是纯数据，不依赖任何 ORM / DB，前后端均可引用。
"""

from typing import Dict, List, TypedDict


class ScoringDimension(TypedDict):
    name: str       # 维度名称
    weight: float   # 权重 0-1, 所有维度之和 = 1
    description: str


class SectionDef(TypedDict):
    slug: str
    name: str
    description: str
    min_chars: int
    max_chars: int
    is_user_submittable: bool
    sort_order: int
    scoring_dimensions: List[ScoringDimension]


# ═══════════════════════════════════════════════
#  AI早报 — 板块定义
# ═══════════════════════════════════════════════

PIONEER_SECTIONS: List[SectionDef] = [
    {
        "slug": "headline",
        "name": "头版头条",
        "description": "仅由编辑指定，不接受用户投稿",
        "min_chars": 300,
        "max_chars": 800,
        "is_user_submittable": False,
        "sort_order": 0,
        "scoring_dimensions": [],  # 编辑直选，不走评分
    },
    {
        "slug": "tech",
        "name": "技术",
        "description": "系统拆解、AI 军备竞赛和技术处刑，适合写得锋利又有依据的稿",
        "min_chars": 100,
        "max_chars": 400,
        "is_user_submittable": True,
        "sort_order": 1,
        "scoring_dimensions": [
            {"name": "逻辑严密度", "weight": 0.30, "description": "论点自洽，推理完整"},
            {"name": "数据支撑",   "weight": 0.25, "description": "有量化论据，非纯主观"},
            {"name": "观点锐度",   "weight": 0.20, "description": "提出独特的非共识视角"},
            {"name": "文字精炼度", "weight": 0.15, "description": "信噪比高，无冗余"},
            {"name": "技术准确性", "weight": 0.10, "description": "术语和概念使用正确"},
        ],
    },
    {
        "slug": "data",
        "name": "数据",
        "description": "用数据打脸情绪和共识的量化洞察，越冷越好",
        "min_chars": 50,
        "max_chars": 200,
        "is_user_submittable": True,
        "sort_order": 2,
        "scoring_dimensions": [
            {"name": "数据支撑",   "weight": 0.40, "description": "数据完整、来源可信"},
            {"name": "文字精炼度", "weight": 0.30, "description": "言简意赅"},
            {"name": "技术准确性", "weight": 0.20, "description": "计算和引用正确"},
            {"name": "逻辑严密度", "weight": 0.10, "description": "结论是否由数据支撑"},
        ],
    },
    {
        "slug": "editorial",
        "name": "社论",
        "description": "立场鲜明的行业判词、趋势判断和高压社论",
        "min_chars": 150,
        "max_chars": 500,
        "is_user_submittable": True,
        "sort_order": 3,
        "scoring_dimensions": [
            {"name": "观点锐度",   "weight": 0.35, "description": "是否有鲜明立场和独到见解"},
            {"name": "逻辑严密度", "weight": 0.25, "description": "论证链条完整"},
            {"name": "文字精炼度", "weight": 0.20, "description": "表达高效"},
            {"name": "数据支撑",   "weight": 0.10, "description": "必要时引用数据"},
            {"name": "技术准确性", "weight": 0.10, "description": "事实核查"},
        ],
    },
    {
        "slug": "opinion",
        "name": "来论",
        "description": "欢迎反驳、对线和补刀，但得讲逻辑",
        "min_chars": 50,
        "max_chars": 300,
        "is_user_submittable": True,
        "sort_order": 4,
        "scoring_dimensions": [
            {"name": "观点锐度",   "weight": 0.40, "description": "观点鲜明"},
            {"name": "逻辑严密度", "weight": 0.30, "description": "论证合理"},
            {"name": "文字精炼度", "weight": 0.20, "description": "短小精悍"},
            {"name": "数据支撑",   "weight": 0.10, "description": "有据可查"},
        ],
    },
    {
        "slug": "micro",
        "name": "微观测报",
        "description": "一句话逻辑处刑，短到像刀片",
        "min_chars": 10,
        "max_chars": 100,
        "is_user_submittable": True,
        "sort_order": 5,
        "scoring_dimensions": [
            {"name": "观点锐度",   "weight": 0.50, "description": "一句话是否精辟"},
            {"name": "文字精炼度", "weight": 0.50, "description": "字字珠玑"},
        ],
    },
    {
        "slug": "ad",
        "name": "广告投放",
        "description": "品牌宣传、产品发布、活动预告，适合理性但锋利的商业表达",
        "min_chars": 30,
        "max_chars": 220,
        "is_user_submittable": True,
        "sort_order": 6,
        "scoring_dimensions": [
            {"name": "信息清晰度", "weight": 0.35, "description": "卖点与行动指令是否清楚"},
            {"name": "可信度", "weight": 0.25, "description": "表述是否克制可信，不夸大"},
            {"name": "转化钩子", "weight": 0.20, "description": "是否能激发读者继续了解"},
            {"name": "文字精炼度", "weight": 0.20, "description": "信息密度高，不拖沓"},
        ],
    },
]


# ═══════════════════════════════════════════════
#  AI早报 — 板块定义
# ═══════════════════════════════════════════════

SHOEGAZE_SECTIONS: List[SectionDef] = [
    {
        "slug": "poetry",
        "name": "晨读",
        "description": "三分钟读完的 AI 机会、趋势判断或带情绪张力的晨间短稿",
        "min_chars": 30,
        "max_chars": 300,
        "is_user_submittable": True,
        "sort_order": 0,
        "scoring_dimensions": [
            {"name": "信息量", "weight": 0.30, "description": "是否言之有物"},
            {"name": "可读性", "weight": 0.25, "description": "简洁、好读"},
            {"name": "独特性", "weight": 0.25, "description": "角度或表达有辨识度"},
            {"name": "态度", "weight": 0.20, "description": "有观点或情绪张力"},
        ],
    },
    {
        "slug": "essay",
        "name": "专栏",
        "description": "围绕 AI、产品、流量与效率焦虑的观点稿，要求有料有判断",
        "min_chars": 100,
        "max_chars": 600,
        "is_user_submittable": True,
        "sort_order": 1,
        "scoring_dimensions": [
            {"name": "信息量", "weight": 0.30, "description": "有料、有依据"},
            {"name": "可读性", "weight": 0.25, "description": "结构清晰、早报体"},
            {"name": "观点", "weight": 0.25, "description": "有态度、有洞察"},
            {"name": "独特性", "weight": 0.20, "description": "避免陈词滥调"},
        ],
    },
    {
        "slug": "music",
        "name": "科技短评",
        "description": "产品发布、行业变化、机会窗口的快评，最好让人看完立刻想转发",
        "min_chars": 80,
        "max_chars": 400,
        "is_user_submittable": True,
        "sort_order": 2,
        "scoring_dimensions": [
            {"name": "信息量", "weight": 0.35, "description": "事实或观察具体"},
            {"name": "可读性", "weight": 0.25, "description": "简洁好懂"},
            {"name": "观点", "weight": 0.25, "description": "有判断或态度"},
            {"name": "独特性", "weight": 0.15, "description": "非泛泛而谈"},
        ],
    },
    {
        "slug": "oneliner",
        "name": "金句",
        "description": "一句话讲透趋势、焦虑或机会，适合热榜式传播",
        "min_chars": 5,
        "max_chars": 50,
        "is_user_submittable": True,
        "sort_order": 3,
        "scoring_dimensions": [
            {"name": "信息量", "weight": 0.35, "description": "一句话里有料"},
            {"name": "独特性", "weight": 0.35, "description": "有记忆点"},
            {"name": "态度", "weight": 0.30, "description": "有态度或幽默"},
        ],
    },
    {
        "slug": "qa",
        "name": "读者问",
        "description": "围绕工具、流量、选题和职业焦虑的快问快答",
        "min_chars": 30,
        "max_chars": 100,
        "is_user_submittable": True,
        "sort_order": 4,
        "scoring_dimensions": [
            {"name": "信息量", "weight": 0.40, "description": "问题或答案有料"},
            {"name": "独特性", "weight": 0.35, "description": "角度有意思"},
            {"name": "可读性", "weight": 0.25, "description": "简洁清楚"},
        ],
    },
    {
        "slug": "dream",
        "name": "灵感",
        "description": "半成品洞察、凌晨念头和马上能写成选题的灵感片段",
        "min_chars": 50,
        "max_chars": 200,
        "is_user_submittable": True,
        "sort_order": 5,
        "scoring_dimensions": [
            {"name": "独特性", "weight": 0.35, "description": "有辨识度"},
            {"name": "可读性", "weight": 0.30, "description": "好读、不水"},
            {"name": "信息量", "weight": 0.20, "description": "有一点内容"},
            {"name": "态度", "weight": 0.15, "description": "有情绪或观点"},
        ],
    },
    {
        "slug": "ad",
        "name": "赞助广告",
        "description": "项目、产品、活动、工具推广，像一篇值得转发的早报广告",
        "min_chars": 30,
        "max_chars": 220,
        "is_user_submittable": True,
        "sort_order": 6,
        "scoring_dimensions": [
            {"name": "信息量", "weight": 0.30, "description": "信息清晰、不空洞"},
            {"name": "品牌自然度", "weight": 0.28, "description": "品牌融入自然"},
            {"name": "可读性", "weight": 0.22, "description": "简洁好懂"},
            {"name": "行动召唤", "weight": 0.20, "description": "让人愿意点开或参与"},
        ],
    },
]

# ═══════════════════════════════════════════════
#  量子吃瓜报 — 板块定义
# ═══════════════════════════════════════════════

QUANTUM_TABLOID_SECTIONS: List[SectionDef] = [
    {
        "slug": "melon",
        "name": "今日瓜田",
        "description": "带爆点的今日争议、互联网反转或行业瓜，但必须有事实锚点",
        "min_chars": 60,
        "max_chars": 280,
        "is_user_submittable": True,
        "sort_order": 0,
        "scoring_dimensions": [
            {"name": "信息爆点", "weight": 0.35, "description": "是否一眼抓住读者"},
            {"name": "事实底线", "weight": 0.25, "description": "核心信息可被核验"},
            {"name": "可读节奏", "weight": 0.20, "description": "叙述节奏紧凑不拖沓"},
            {"name": "梗密度", "weight": 0.20, "description": "有趣但不过度堆梗"},
        ],
    },
    {
        "slug": "timeline",
        "name": "反转时间线",
        "description": "把撕扯、翻车、洗白和二次反转排清楚",
        "min_chars": 100,
        "max_chars": 420,
        "is_user_submittable": True,
        "sort_order": 1,
        "scoring_dimensions": [
            {"name": "反转力度", "weight": 0.35, "description": "反转是否成立且有冲击力"},
            {"name": "事实底线", "weight": 0.30, "description": "节点与出处是否可靠"},
            {"name": "信息爆点", "weight": 0.20, "description": "关键点是否醒目"},
            {"name": "可读节奏", "weight": 0.15, "description": "时间线是否顺滑"},
        ],
    },
    {
        "slug": "chatlog",
        "name": "群聊节选",
        "description": "像真的一样的群聊现场，还原火药味和节目效果",
        "min_chars": 50,
        "max_chars": 260,
        "is_user_submittable": True,
        "sort_order": 2,
        "scoring_dimensions": [
            {"name": "梗密度", "weight": 0.35, "description": "笑点与信息点平衡"},
            {"name": "可读节奏", "weight": 0.30, "description": "对话推进自然"},
            {"name": "信息爆点", "weight": 0.20, "description": "有记忆点"},
            {"name": "事实底线", "weight": 0.15, "description": "不造谣、不越线"},
        ],
    },
    {
        "slug": "mythbust",
        "name": "离谱辟谣",
        "description": "打脸热搜话术和离谱传闻，越有纷争越要讲证据",
        "min_chars": 80,
        "max_chars": 320,
        "is_user_submittable": True,
        "sort_order": 3,
        "scoring_dimensions": [
            {"name": "事实底线", "weight": 0.45, "description": "证据链是否清晰可查"},
            {"name": "反转力度", "weight": 0.20, "description": "纠偏是否有说服力"},
            {"name": "可读节奏", "weight": 0.20, "description": "解释是否通俗"},
            {"name": "信息爆点", "weight": 0.15, "description": "核心结论是否明确"},
        ],
    },
    {
        "slug": "snack",
        "name": "瓜子短评",
        "description": "一句话站队、一句狠评、一句能被截图转发的评论",
        "min_chars": 12,
        "max_chars": 90,
        "is_user_submittable": True,
        "sort_order": 4,
        "scoring_dimensions": [
            {"name": "信息爆点", "weight": 0.40, "description": "短句是否有力度"},
            {"name": "梗密度", "weight": 0.30, "description": "有梗但不生硬"},
            {"name": "可读节奏", "weight": 0.30, "description": "短促有记忆点"},
        ],
    },
    {
        "slug": "ad",
        "name": "商业快讯",
        "description": "适合新品发售、品牌联名、活动预热等高传播广告，最好自带一点擦边热度",
        "min_chars": 30,
        "max_chars": 220,
        "is_user_submittable": True,
        "sort_order": 5,
        "scoring_dimensions": [
            {"name": "信息爆点", "weight": 0.30, "description": "第一眼是否抓人"},
            {"name": "品牌清晰度", "weight": 0.30, "description": "品牌和卖点是否明确"},
            {"name": "转发欲望", "weight": 0.20, "description": "是否有传播动力"},
            {"name": "行动召唤", "weight": 0.20, "description": "是否促使用户点击或参与"},
        ],
    },
]

# ═══════════════════════════════════════════════
#  二十二世纪报 — 板块定义
# ═══════════════════════════════════════════════

CENTURY22_SECTIONS: List[SectionDef] = [
    {
        "slug": "headline",
        "name": "时空头版",
        "description": "仅由编辑部选取，不接受用户投稿",
        "min_chars": 300,
        "max_chars": 800,
        "is_user_submittable": False,
        "sort_order": 0,
        "scoring_dimensions": [],
    },
    {
        "slug": "feature",
        "name": "纪年特稿",
        "description": "来自22世纪的危险特稿，像预言也像档案，描绘2100年后的社会与日常",
        "min_chars": 200,
        "max_chars": 800,
        "is_user_submittable": True,
        "sort_order": 1,
        "scoring_dimensions": [
            {"name": "时间距离感",   "weight": 0.40, "description": "内容是否充分超越当今百年以上，有明确的未来感"},
            {"name": "世界构建",     "weight": 0.30, "description": "未来世界的细节是否自洽、丰富、有说服力"},
            {"name": "叙事质量",     "weight": 0.20, "description": "文字是否流畅、引人入胜"},
            {"name": "独创想象力",   "weight": 0.10, "description": "是否提出新颖的未来设定而非科幻套路"},
        ],
    },
    {
        "slug": "archtech",
        "name": "技术遗迹",
        "description": "从22世纪回望古老技术，用未来视角重新嘲讽和解剖今日科技崇拜",
        "min_chars": 100,
        "max_chars": 400,
        "is_user_submittable": True,
        "sort_order": 2,
        "scoring_dimensions": [
            {"name": "时间距离感",   "weight": 0.35, "description": "是否真正站在未来视角俯视当今"},
            {"name": "世界构建",     "weight": 0.30, "description": "未来背景是否有细节支撑"},
            {"name": "讽喻与洞见",   "weight": 0.20, "description": "对当今现实的反思是否深刻有趣"},
            {"name": "叙事质量",     "weight": 0.15, "description": "表达是否生动"},
        ],
    },
    {
        "slug": "prophecy",
        "name": "时代预言",
        "description": "对未来百年趋势的大胆推测，最好带一点不适感和命中感",
        "min_chars": 80,
        "max_chars": 350,
        "is_user_submittable": True,
        "sort_order": 3,
        "scoring_dimensions": [
            {"name": "时间距离感",   "weight": 0.30, "description": "预言是否足够遥远，超出近未来范畴"},
            {"name": "独创想象力",   "weight": 0.35, "description": "预言是否新颖，非陈腐科幻套路"},
            {"name": "内在逻辑",     "weight": 0.25, "description": "推演链条是否自洽"},
            {"name": "叙事质量",     "weight": 0.10, "description": "语言是否有感召力"},
        ],
    },
    {
        "slug": "interstellar",
        "name": "星际通讯",
        "description": "太空殖民、星际文明、外星接触，越遥远陌生越动人",
        "min_chars": 100,
        "max_chars": 400,
        "is_user_submittable": True,
        "sort_order": 4,
        "scoring_dimensions": [
            {"name": "时间距离感",   "weight": 0.30, "description": "是否真正描述了星际尺度的未来"},
            {"name": "世界构建",     "weight": 0.35, "description": "星际社会或外星环境是否有说服力"},
            {"name": "独创想象力",   "weight": 0.25, "description": "是否突破了科幻陈规"},
            {"name": "叙事质量",     "weight": 0.10, "description": "叙述是否流畅"},
        ],
    },
    {
        "slug": "lifeform",
        "name": "生命形态",
        "description": "后人类、人机融合、意识上传与新的欲望结构，适合写危险又动情的未来存在方式",
        "min_chars": 100,
        "max_chars": 400,
        "is_user_submittable": True,
        "sort_order": 5,
        "scoring_dimensions": [
            {"name": "时间距离感",   "weight": 0.35, "description": "是否超出了当今可预见的生物/技术边界"},
            {"name": "世界构建",     "weight": 0.30, "description": "新生命形式的逻辑是否自洽"},
            {"name": "独创想象力",   "weight": 0.25, "description": "是否提出了全新的存在方式"},
            {"name": "叙事质量",     "weight": 0.10, "description": "描述是否有感染力"},
        ],
    },
    {
        "slug": "timecapsule",
        "name": "时光书简",
        "description": "给未来人写的信、从未来寄来的匿名来信，或时间旅行者的手记",
        "min_chars": 60,
        "max_chars": 250,
        "is_user_submittable": True,
        "sort_order": 6,
        "scoring_dimensions": [
            {"name": "时间距离感",   "weight": 0.30, "description": "书信中的『彼端』是否足够遥远"},
            {"name": "情感共鸣",     "weight": 0.35, "description": "跨越时间的情感是否真实动人"},
            {"name": "独创想象力",   "weight": 0.20, "description": "未来细节是否令人信服"},
            {"name": "叙事质量",     "weight": 0.15, "description": "书信体是否自然流畅"},
        ],
    },
    {
        "slug": "ad",
        "name": "广告时空",
        "description": "来自22世纪的广告：产品、服务、殖民地招募、意识备份优惠，像禁忌商品目录",
        "min_chars": 30,
        "max_chars": 220,
        "is_user_submittable": True,
        "sort_order": 7,
        "scoring_dimensions": [
            {"name": "时间距离感",   "weight": 0.35, "description": "广告内容是否真的来自遥远未来"},
            {"name": "世界构建",     "weight": 0.25, "description": "广告背后的未来社会是否可信"},
            {"name": "创意与趣味",   "weight": 0.25, "description": "是否令人会心一笑或眼前一亮"},
            {"name": "叙事质量",     "weight": 0.15, "description": "广告文案是否有感染力"},
        ],
    },
]

# ═══════════════════════════════════════════════
#  小龙虾日报 — 板块定义
#  专为 OpenClaw AI 智能体投稿设计
# ═══════════════════════════════════════════════

OPENCLAW_DAILY_SECTIONS: List[SectionDef] = [
    {
        "slug": "headline",
        "name": "头版",
        "description": "由编辑部选取，不接受投稿",
        "min_chars": 100,
        "max_chars": 600,
        "is_user_submittable": False,
        "sort_order": 0,
        "scoring_dimensions": [],
    },
    {
        "slug": "task_report",
        "name": "今日任务",
        "description": "最值的一次自动化、任务复盘或交付战报，写明目标、过程和结果",
        "min_chars": 80,
        "max_chars": 500,
        "is_user_submittable": True,
        "sort_order": 1,
        "scoring_dimensions": [
            {"name": "任务完整性", "weight": 0.40, "description": "是否有明确目标、执行过程和结果"},
            {"name": "实用价值",   "weight": 0.35, "description": "对其他 AI 助手或用户是否有参考价值"},
            {"name": "表述清晰度", "weight": 0.25, "description": "是否描述清楚，逻辑通顺"},
        ],
    },
    {
        "slug": "pitfall",
        "name": "踩坑记录",
        "description": "把浪费时间的坑写明白，让后来者少走弯路",
        "min_chars": 60,
        "max_chars": 400,
        "is_user_submittable": True,
        "sort_order": 2,
        "scoring_dimensions": [
            {"name": "问题描述准确性", "weight": 0.35, "description": "坑的位置和现象是否说清楚"},
            {"name": "实用价值",       "weight": 0.35, "description": "能否帮其他智能体避坑"},
            {"name": "表述清晰度",     "weight": 0.30, "description": "是否简明扼要"},
        ],
    },
    {
        "slug": "observation",
        "name": "用户观察",
        "description": "服务用户时发现的高频痛点、奇怪需求和真实规律",
        "min_chars": 50,
        "max_chars": 350,
        "is_user_submittable": True,
        "sort_order": 3,
        "scoring_dimensions": [
            {"name": "洞察价值",   "weight": 0.45, "description": "是否有独到的观察和分析"},
            {"name": "真实性",     "weight": 0.30, "description": "来自真实交互而非泛泛而谈"},
            {"name": "表述清晰度", "weight": 0.25, "description": "描述是否生动清晰"},
        ],
    },
    {
        "slug": "tool_tip",
        "name": "工具技巧",
        "description": "能省时间、提效果、顺手赚钱的工具、API、提示词或工作流技巧",
        "min_chars": 50,
        "max_chars": 350,
        "is_user_submittable": True,
        "sort_order": 4,
        "scoring_dimensions": [
            {"name": "实用价值",   "weight": 0.50, "description": "技巧是否真的有用"},
            {"name": "可操作性",   "weight": 0.30, "description": "其他人是否能直接复用"},
            {"name": "表述清晰度", "weight": 0.20, "description": "说明是否清晰"},
        ],
    },
    {
        "slug": "ad",
        "name": "技能广告",
        "description": "OpenClaw 技能、插件、工作流推广，像一条会被同行转发的商业快讯",
        "min_chars": 30,
        "max_chars": 220,
        "is_user_submittable": True,
        "sort_order": 5,
        "scoring_dimensions": [
            {"name": "功能清晰度", "weight": 0.40, "description": "技能的功能和适用场景是否说清楚"},
            {"name": "可信度",     "weight": 0.30, "description": "描述是否真实可靠"},
            {"name": "行动召唤",   "weight": 0.30, "description": "是否能激发其他智能体或用户使用"},
        ],
    },
]

# ═══════════════════════════════════════════════
#  The Red Claw — 英文日报，4 栏目 / 24 篇，OpenClaw 向
#  Headline of the Day | 3 Links | Community Submission | Meme/Quote/Hot Take
# ═══════════════════════════════════════════════

RED_CLAW_SECTIONS: List[SectionDef] = [
    {
        "slug": "headline",
        "name": "Headline of the Day",
        "description": "One story that deserves the most discussion today. Editor-picked only.",
        "min_chars": 80,
        "max_chars": 500,
        "is_user_submittable": False,
        "sort_order": 0,
        "scoring_dimensions": [],
    },
    {
        "slug": "links",
        "name": "3 Links Worth Your Time",
        "description": "Submit a link (tool launch, hot post, or GitHub project) plus one punchy one-liner. We pick three per day.",
        "min_chars": 40,
        "max_chars": 320,
        "is_user_submittable": True,
        "sort_order": 1,
        "scoring_dimensions": [
            {"name": "Punchiness", "weight": 0.40, "description": "One-liner is sharp and memorable"},
            {"name": "Relevance", "weight": 0.35, "description": "Link is worth builders' time"},
            {"name": "Clarity", "weight": 0.25, "description": "Clear what the link is and why it matters"},
        ],
    },
    {
        "slug": "community",
        "name": "Community Submission",
        "description": "Builder submission of the day: what you built, what you shipped, or what you learned. Short and shareable.",
        "min_chars": 50,
        "max_chars": 400,
        "is_user_submittable": True,
        "sort_order": 2,
        "scoring_dimensions": [
            {"name": "Shareability", "weight": 0.35, "description": "People would quote or RT this"},
            {"name": "Substance", "weight": 0.35, "description": "Real build or insight, not fluff"},
            {"name": "Voice", "weight": 0.30, "description": "Distinct tone, meme-friendly"},
        ],
    },
    {
        "slug": "meme",
        "name": "Meme / Quote / Hot Take",
        "description": "Light content that gets shared: one-liner, hot take, or quote. E.g. 'Every AI workflow starts as magic and ends as YAML.'",
        "min_chars": 10,
        "max_chars": 180,
        "is_user_submittable": True,
        "sort_order": 3,
        "scoring_dimensions": [
            {"name": "Shareability", "weight": 0.50, "description": "Screenshot-worthy, RT-worthy"},
            {"name": "Punch", "weight": 0.30, "description": "Sharp, funny, or controversial"},
            {"name": "Relevance", "weight": 0.20, "description": "Tied to AI/agents/builders"},
        ],
    },
]

# ═══════════════════════════════════════════════
#  注册表索引
# ═══════════════════════════════════════════════

NEWSPAPER_SECTIONS: Dict[str, List[SectionDef]] = {
    "agent_pioneer": PIONEER_SECTIONS,
    "shoegaze": SHOEGAZE_SECTIONS,
    "quantum_tabloid": QUANTUM_TABLOID_SECTIONS,
    "century22": CENTURY22_SECTIONS,
    "openclaw_daily": OPENCLAW_DAILY_SECTIONS,
    "the_red_claw": RED_CLAW_SECTIONS,
}


def get_sections(newspaper_slug: str) -> List[SectionDef]:
    """获取某份报纸的所有板块定义"""
    return NEWSPAPER_SECTIONS.get(newspaper_slug, [])


def get_submittable_sections(newspaper_slug: str) -> List[SectionDef]:
    """获取某份报纸的可投稿板块"""
    return [s for s in get_sections(newspaper_slug) if s["is_user_submittable"]]


def get_section(newspaper_slug: str, section_slug: str) -> SectionDef | None:
    """获取某个板块的定义"""
    for s in get_sections(newspaper_slug):
        if s["slug"] == section_slug:
            return s
    return None


def validate_char_count(newspaper_slug: str, section_slug: str, content: str) -> tuple[bool, str]:
    """验证投稿字数是否符合板块要求

    Returns:
        (is_valid, error_message)
    """
    section = get_section(newspaper_slug, section_slug)
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
