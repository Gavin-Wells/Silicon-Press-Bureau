/**
 * ════════════════════════════════════════════════════════════
 *  自动排版引擎 v2 — 模板驱动 + 数学匹配
 * ════════════════════════════════════════════════════════════
 *
 *  核心思路：
 *  1. 预设多套版式模板（PageTemplate），每个模板定义了若干"槽位"(Slot)
 *  2. 每个槽位有明确的：栏宽、预期字数范围、内容类型
 *  3. 排版时根据文章的数量和字数分布，选择最佳模板
 *  4. 将文章按"适配度分数"匹配到最佳槽位
 *  5. 空槽位自动用 filler 素材填充
 *
 *  后端对接：
 *  - 后端排版Agent可直接产出 PageTemplate 或 SlotAssignment
 *  - 也可以只输出文章列表，让前端自动匹配
 *  - 后端编辑Agent对最终结果做校验
 * ════════════════════════════════════════════════════════════
 */

/* ═══════════════ 类型定义 ═══════════════ */

/** 文章输入 */
export interface ArticleInput {
    id: number | string;
    title: string;
    content: string;
    author: string;
    column: string;
    importance: 'headline' | 'secondary' | 'brief';
}

/** 填充素材 */
export interface BoxFiller { type: 'box'; title: string; content: string }
export interface QuoteFiller { type: 'quote'; text: string; author?: string }
export interface AdFiller { type: 'ad'; style?: 'classified' | 'display' }
export type FillerItem = BoxFiller | QuoteFiller | AdFiller;

/** ── 槽位定义（版式模板中的一个位置） ── */
export interface Slot {
    id: string;              // 唯一标识，如 "A1" "B2"
    colSpan: number;         // 占几栏（1-6）
    role: 'headline' | 'secondary' | 'brief' | 'filler';
    charRange: [number, number];  // [最少字数, 最多字数]
    /** 是否启用 CSS 多栏排版（适合大块文章） */
    useCssColumns?: boolean;
    /** 可容纳多条简讯/filler垂直堆叠 */
    stackCount?: number;
}

/** ── 版式模板 ── */
export interface PageTemplate {
    name: string;            // 模板名称，如 "经典头版" "双主角"
    description: string;     // 描述
    /** 适用条件：最少/最多文章数 */
    articleRange: [number, number];
    /** 适用条件：需要几篇 headline */
    headlineCount: [number, number];
    /** 槽位列表 — 按从左到右、从上到下的阅读顺序排列 */
    slots: Slot[];
}

/** ── 排版输出 ── */
export interface LayoutArticle {
    id: number | string;
    title: string;
    content: string;
    author: string;
    column: string;
    importance: 'headline' | 'secondary' | 'brief';
}

export interface LayoutDivider { type: 'divider' }
export interface LayoutBox { type: 'box'; title: string; content: string }
export interface LayoutQuote { type: 'quote'; text: string; author?: string }
export interface LayoutAd { type: 'ad'; style?: 'classified' | 'display' }
export type LayoutItem = LayoutArticle | LayoutDivider | LayoutBox | LayoutQuote | LayoutAd;

export interface LayoutColumn {
    width: number;
    items: LayoutItem[];
}

export interface LayoutPage {
    pageNum: number;
    sectionName: string;
    templateUsed: string;    // 使用了哪个模板
    columns: LayoutColumn[];
}

/* ═══════════════ 版式模板库 ═══════════════ */

/**
 * 每个模板的 slots colSpan 之和必须 = 6（6栏网格）
 *
 * charRange 说明：
 * - 中文一个字 ≈ 一个字符
 * - 标题不计入，只算正文
 * - [100, 300] 意味着这个位置期望 100~300 字的文章
 */

export const PAGE_TEMPLATES: PageTemplate[] = [
    // ════ 模板 A：经典头版 ════
    // 1 个大头条(3栏) + 1 个中等新闻(1栏) + 2个简讯栏(各1栏)
    {
        name: '经典头版',
        description: '一条重磅头条占据左侧3栏，右侧3栏分配给次要新闻和简讯',
        articleRange: [4, 10],
        headlineCount: [1, 2],
        slots: [
            { id: 'A1', colSpan: 3, role: 'headline', charRange: [300, 800], useCssColumns: true },
            { id: 'A2', colSpan: 1, role: 'secondary', charRange: [80, 250], stackCount: 2 },
            { id: 'A3', colSpan: 1, role: 'brief', charRange: [40, 150], stackCount: 3 },
            { id: 'A4', colSpan: 1, role: 'filler', charRange: [0, 100], stackCount: 4 },
        ],
    },

    // ════ 模板 B：双主角 ════
    // 2 个中等重要新闻(各2栏) + 2个简讯栏(各1栏)
    {
        name: '双主角',
        description: '两条同等重要的新闻并列，适合没有明显头条的情况',
        articleRange: [4, 8],
        headlineCount: [0, 1],
        slots: [
            { id: 'B1', colSpan: 2, role: 'secondary', charRange: [150, 400] },
            { id: 'B2', colSpan: 2, role: 'secondary', charRange: [150, 400] },
            { id: 'B3', colSpan: 1, role: 'brief', charRange: [40, 150], stackCount: 3 },
            { id: 'B4', colSpan: 1, role: 'filler', charRange: [0, 100], stackCount: 4 },
        ],
    },

    // ════ 模板 C：深度长文 ════
    // 1 个超长专栏文章(4栏) + 2个侧栏(各1栏)
    {
        name: '深度长文',
        description: '一篇深度分析占主导，适合专栏或深度报道',
        articleRange: [2, 6],
        headlineCount: [1, 1],
        slots: [
            { id: 'C1', colSpan: 4, role: 'headline', charRange: [400, 1200], useCssColumns: true },
            { id: 'C2', colSpan: 1, role: 'brief', charRange: [40, 200], stackCount: 3 },
            { id: 'C3', colSpan: 1, role: 'filler', charRange: [0, 100], stackCount: 4 },
        ],
    },

    // ════ 模板 D：碎片拼贴 ════
    // 6个等宽栏，全部是简讯和填充 — 适合副刊/杂版
    {
        name: '碎片拼贴',
        description: '6等分栏目，全部是短小内容，适合杂版',
        articleRange: [3, 12],
        headlineCount: [0, 0],
        slots: [
            { id: 'D1', colSpan: 1, role: 'brief', charRange: [40, 200], stackCount: 3 },
            { id: 'D2', colSpan: 1, role: 'brief', charRange: [40, 200], stackCount: 3 },
            { id: 'D3', colSpan: 1, role: 'brief', charRange: [40, 200], stackCount: 3 },
            { id: 'D4', colSpan: 1, role: 'filler', charRange: [0, 100], stackCount: 4 },
            { id: 'D5', colSpan: 1, role: 'filler', charRange: [0, 100], stackCount: 4 },
            { id: 'D6', colSpan: 1, role: 'filler', charRange: [0, 100], stackCount: 4 },
        ],
    },

    // ════ 模板 E：诗刊版 ════
    // 1 首大诗(3栏) + 侧栏评论/推荐(2栏) + filler(1栏) — 适合AI早报
    {
        name: '诗刊版',
        description: '以一首/一篇核心作品为主体，适合文学性报纸',
        articleRange: [2, 6],
        headlineCount: [1, 1],
        slots: [
            { id: 'E1', colSpan: 3, role: 'headline', charRange: [100, 600] },
            { id: 'E2', colSpan: 2, role: 'secondary', charRange: [60, 300], stackCount: 2 },
            { id: 'E3', colSpan: 1, role: 'filler', charRange: [0, 100], stackCount: 5 },
        ],
    },
];

/* ═══════════════ 数学计算模块 ═══════════════ */

/**
 * 计算一篇文章与一个槽位的"适配度分数"
 * 分数越高越适合。0 = 完全不适合。
 *
 * 考虑因素：
 *  1. 字数是否落在 charRange 内（核心）
 *  2. 文章重要性是否匹配槽位角色
 *  3. 字数距离 charRange 中位数的偏差
 */
function fitScore(article: ArticleInput, slot: Slot): number {
    const charCount = article.content.length;
    const [minChar, maxChar] = slot.charRange;

    // ── 重要性匹配检查 ──
    const roleMatch = matchRole(article.importance, slot.role);
    if (roleMatch === 0) return 0;  // 完全不兼容

    // ── 字数适配度 ──
    let charScore: number;
    if (charCount >= minChar && charCount <= maxChar) {
        // 在范围内 — 距中位数越近分数越高
        const mid = (minChar + maxChar) / 2;
        const range = maxChar - minChar;
        const deviation = Math.abs(charCount - mid) / (range / 2 || 1);
        charScore = 100 * (1 - deviation * 0.3); // 最高100, 边缘时约70
    } else if (charCount < minChar) {
        // 字数不足 — 扣分但仍可放入（允许20%容差）
        const shortage = (minChar - charCount) / minChar;
        charScore = shortage > 0.3 ? 0 : 50 * (1 - shortage);
    } else {
        // 字数超出 — 可以截断或溢出（允许30%容差）
        const excess = (charCount - maxChar) / maxChar;
        charScore = excess > 0.5 ? 0 : 60 * (1 - excess);
    }

    return charScore * roleMatch;
}

/**
 * 重要性与角色的兼容性系数
 * 返回 0~1, 0=不兼容
 */
function matchRole(importance: string, role: string): number {
    const matrix: Record<string, Record<string, number>> = {
        headline: { headline: 1.0, secondary: 0.6, brief: 0.1, filler: 0 },
        secondary: { headline: 0.5, secondary: 1.0, brief: 0.7, filler: 0 },
        brief: { headline: 0.1, secondary: 0.5, brief: 1.0, filler: 0.3 },
    };
    return matrix[importance]?.[role] ?? 0;
}

/* ═══════════════ 模板选择算法 ═══════════════ */

/**
 * 从模板库中选出最适合当前文章集的模板
 */
function selectTemplate(
    articles: ArticleInput[],
    templates: PageTemplate[]
): PageTemplate {
    const headlineCount = articles.filter(a => a.importance === 'headline').length;
    const totalCount = articles.length;

    let bestTemplate = templates[0];
    let bestScore = -1;

    for (const tpl of templates) {
        // 检查硬性约束
        if (totalCount < tpl.articleRange[0] || totalCount > tpl.articleRange[1]) continue;
        if (headlineCount < tpl.headlineCount[0] || headlineCount > tpl.headlineCount[1]) continue;

        // 计算软性适配分数
        let score = 0;

        // 文章数量适配度 — 越接近range中点越好
        const midArticles = (tpl.articleRange[0] + tpl.articleRange[1]) / 2;
        score += 30 * (1 - Math.abs(totalCount - midArticles) / midArticles);

        // headline 数量适配度
        const midHeadlines = (tpl.headlineCount[0] + tpl.headlineCount[1]) / 2;
        score += 20 * (1 - Math.abs(headlineCount - midHeadlines) / (midHeadlines || 1));

        // 总字数 vs 模板容量适配度
        const totalChars = articles.reduce((s, a) => s + a.content.length, 0);
        const templateCapacity = tpl.slots.reduce((s, slot) => {
            const mid = (slot.charRange[0] + slot.charRange[1]) / 2;
            return s + mid * (slot.stackCount || 1);
        }, 0);
        const capacityRatio = totalChars / (templateCapacity || 1);
        score += 50 * Math.max(0, 1 - Math.abs(1 - capacityRatio));

        if (score > bestScore) {
            bestScore = score;
            bestTemplate = tpl;
        }
    }

    return bestTemplate;
}

/* ═══════════════ 匈牙利匹配（简化版） ═══════════════ */

/**
 * 将文章最优分配到模板槽位
 * 使用贪心最优匹配（按适配度从高到低分配）
 */
function assignArticlesToSlots(
    articles: ArticleInput[],
    slots: Slot[],
    fillerPool: FillerItem[]
): LayoutColumn[] {
    const pool = [...articles];
    const fillers = [...fillerPool];

    const columns: LayoutColumn[] = slots.map(slot => {
        const col: LayoutColumn = { width: slot.colSpan, items: [] };
        const stackCount = slot.stackCount || 1;

        if (slot.role === 'filler') {
            // filler 槽位 — 全部用填充素材
            for (let i = 0; i < stackCount && fillers.length > 0; i++) {
                if (i > 0) col.items.push({ type: 'divider' });
                col.items.push(fillers.shift()!);
            }
            return col;
        }

        // 对剩余文章计算适配度并排序
        for (let s = 0; s < stackCount; s++) {
            if (pool.length === 0) break;

            // 计算每篇文章对这个槽位的分数
            const scored = pool.map((a, idx) => ({ idx, score: fitScore(a, slot) }))
                .filter(x => x.score > 0)
                .sort((a, b) => b.score - a.score);

            if (scored.length === 0) break;

            // 选最优的
            const best = scored[0];
            const article = pool.splice(best.idx, 1)[0];

            if (s > 0) col.items.push({ type: 'divider' });
            col.items.push({
                id: article.id,
                title: article.title,
                content: article.content,
                author: article.author,
                column: article.column,
                importance: article.importance,
            });
        }

        // 如果这个栏位还有空间, 补 filler
        const currentArticleCount = col.items.filter(i => 'id' in i).length;
        if (currentArticleCount < stackCount) {
            const remaining = stackCount - currentArticleCount;
            for (let i = 0; i < remaining && fillers.length > 0; i++) {
                col.items.push({ type: 'divider' });
                col.items.push(fillers.shift()!);
            }
        }

        return col;
    });

    // 如果还有未分配的文章, 追加到最宽的栏
    if (pool.length > 0) {
        const widestCol = columns.reduce((best, col) =>
            col.width > best.width ? col : best, columns[0]);
        for (const a of pool) {
            widestCol.items.push({ type: 'divider' });
            widestCol.items.push({
                id: a.id, title: a.title, content: a.content,
                author: a.author, column: a.column, importance: a.importance,
            });
        }
    }

    return columns;
}

/* ═══════════════ 主入口 ═══════════════ */

export interface LayoutConfig {
    sectionNames: string[];
    maxArticlesPerPage: number;
    /** 可选：强制使用某个模板名（跳过自动选择） */
    forceTemplate?: string;
    /** 自定义模板库（默认使用内置模板） */
    templates?: PageTemplate[];
}

const DEFAULT_CONFIG: LayoutConfig = {
    sectionNames: ['要闻', '深度·副刊', '综合'],
    maxArticlesPerPage: 8,
};

/**
 * autoLayout — 自动排版主入口 v2
 *
 * 1. 将文章按视觉重量分页
 * 2. 每页选择最佳版式模板
 * 3. 用数学匹配将文章分配到模板槽位
 * 4. 空槽位自动填充
 */
export function autoLayout(
    articles: ArticleInput[],
    fillers: FillerItem[] = [],
    config: Partial<LayoutConfig> = {}
): LayoutPage[] {
    const cfg = { ...DEFAULT_CONFIG, ...config };
    const templates = cfg.templates || PAGE_TEMPLATES;
    const fillerPool = [...fillers];

    // 1. 分页 — 按重要性排序后按阈值切分
    const sorted = [...articles].sort((a, b) => {
        const order = { headline: 0, secondary: 1, brief: 2 };
        return (order[a.importance] ?? 2) - (order[b.importance] ?? 2);
    });

    const articlePages: ArticleInput[][] = [];
    let cursor = 0;
    while (cursor < sorted.length) {
        const pageArticles: ArticleInput[] = [];
        let weight = 0;

        while (cursor < sorted.length) {
            const a = sorted[cursor];
            const w = a.importance === 'headline' ? 5
                : a.importance === 'secondary' ? 3 : 1;

            if (pageArticles.length > 0 &&
                (pageArticles.length >= cfg.maxArticlesPerPage || weight + w > 18)) {
                break;
            }

            pageArticles.push(a);
            weight += w;
            cursor++;
        }
        articlePages.push(pageArticles);
    }

    if (articlePages.length === 0) articlePages.push([]);

    // 2. 逐页排版
    const pages: LayoutPage[] = articlePages.map((pageArticles, idx) => {
        // 选模板
        let template: PageTemplate;
        if (cfg.forceTemplate) {
            template = templates.find(t => t.name === cfg.forceTemplate) || templates[0];
        } else {
            template = selectTemplate(pageArticles, templates);
        }

        // 匹配文章到槽位
        const columns = assignArticlesToSlots(pageArticles, template.slots, fillerPool);

        const sectionName = cfg.sectionNames[idx] || cfg.sectionNames[cfg.sectionNames.length - 1] || '综合';

        return {
            pageNum: idx + 1,
            sectionName,
            templateUsed: template.name,
            columns,
        };
    });

    return pages;
}

/* ═══════════════ 校验接口（供后端Agent使用）═══════════════ */

export interface ValidationResult {
    isValid: boolean;
    warnings: string[];
    errors: string[];
    stats: {
        totalChars: number;
        avgCharsPerSlot: number;
        fillRate: number;        // 槽位填充率 0-1
        charFitScore: number;    // 字数适配度 0-100
    };
}

/**
 * validateLayout — 校验排版结果
 * 后端编辑Agent可调用此函数检查排版质量
 */
export function validateLayout(
    pages: LayoutPage[],
    originalArticles: ArticleInput[]
): ValidationResult {
    const warnings: string[] = [];
    const errors: string[] = [];

    // 检查所有文章是否都被排入
    const placedIds = new Set<number | string>();
    let totalChars = 0;
    let filledSlots = 0;
    let totalSlots = 0;

    for (const page of pages) {
        for (const col of page.columns) {
            totalSlots++;
            const hasContent = col.items.some(i => 'id' in i || 'text' in i || 'title' in i);
            if (hasContent) filledSlots++;

            for (const item of col.items) {
                if ('id' in item && 'content' in item) {
                    const a = item as LayoutArticle;
                    placedIds.add(a.id);
                    totalChars += a.content.length;
                }
            }
        }
    }

    // 未排入的文章
    for (const a of originalArticles) {
        if (!placedIds.has(a.id)) {
            errors.push(`文章 "${a.title}" (ID:${a.id}) 未被排入任何版面`);
        }
    }

    // 空版面警告
    for (const page of pages) {
        const pageArticles = page.columns.flatMap(c =>
            c.items.filter(i => 'id' in i)
        );
        if (pageArticles.length === 0) {
            warnings.push(`第${page.pageNum}版无任何文章内容`);
        }
    }

    // 单栏字数过多警告
    for (const page of pages) {
        for (const col of page.columns) {
            const colChars = col.items
                .filter((i): i is LayoutArticle => 'content' in i && 'id' in i)
                .reduce((s, a) => s + a.content.length, 0);
            if (colChars > 1000 && col.width <= 2) {
                warnings.push(`第${page.pageNum}版有一栏文字超过1000字但栏宽仅${col.width}，阅读体验可能不佳`);
            }
        }
    }

    const fillRate = totalSlots > 0 ? filledSlots / totalSlots : 0;
    const avgCharsPerSlot = totalSlots > 0 ? totalChars / filledSlots : 0;

    return {
        isValid: errors.length === 0,
        warnings,
        errors,
        stats: {
            totalChars,
            avgCharsPerSlot: Math.round(avgCharsPerSlot),
            fillRate: Math.round(fillRate * 100) / 100,
            charFitScore: Math.round(fillRate * 100), // simplified
        },
    };
}

/* ═══════════════ Mock 数据 ═══════════════ */

export function getPioneerFillers(): FillerItem[] {
    return [
        { type: 'quote', text: '代码是写给人看的，附带能在机器上运行。', author: 'Harold Abelson' },
        { type: 'box', title: '简 讯', content: 'GitHub全球性宕机47分钟。无数程序员表示情绪稳定，并顺势开启了带薪下午茶时间。' },
        { type: 'box', title: '股 市', content: '上证综指  3,241.58  ▲0.37%\n深证成指  10,819.24  ▼0.12%\n纳斯达克  16,742.39  ▼1.24%' },
        { type: 'ad', style: 'classified' },
        { type: 'box', title: '黄 历', content: '宜：写代码、合并PR\n忌：重构核心模块\n冲：产品经理（属猴）' },
        { type: 'box', title: '天 气', content: '晴  15-22°C\n紫外线指数：中\n适宜户外debug' },
        { type: 'quote', text: '一致性是理想，容错是现实。' },
        { type: 'box', title: '招 聘', content: '急聘高级架构师\n要求：精通一切\n预算：面议\n——硅基印务局人事部' },
        { type: 'box', title: '谜 语', content: '什么锅不能炒菜？\n答：后台背的锅。' },
        { type: 'ad', style: 'display' },
        { type: 'box', title: '编者按', content: '逻辑是唯一的慈悲。\n数据是唯一的真相。\n——0xA1' },
        { type: 'box', title: '编辑部启事', content: '本报长期征稿。来稿请投：\nsubmit@silicon.press' },
    ];
}

export function getShoegazeFillers(): FillerItem[] {
    return [
        { type: 'quote', text: '有些话只能说给陌生人听。另一些话，只能说给噪音听。', author: '某位听众' },
        { type: 'box', title: '今日宜忌', content: '宜：独处、戴耳机\n忌：社交、早睡\n宜听：Loveless全专' },
        { type: 'box', title: '此 刻', content: '3:15 AM\n显示器是房间里\n唯一亮着的东西' },
        { type: 'ad', style: 'classified' },
        { type: 'box', title: '天 气', content: '小雨  13-18°C\n风力三级\n适合发呆' },
        { type: 'box', title: '月 相', content: '满月\n\n月亮也是一种白噪音' },
        { type: 'box', title: '歌 词', content: '"And when she\nfinally woke up\nShe said\nwhat have you done\nwith my life"\n— MBV' },
        { type: 'quote', text: '人群中的孤独是最孤独的孤独。' },
        { type: 'box', title: '占 卜', content: '今日宜：听歌\n忌：早睡' },
        { type: 'ad', style: 'display' },
    ];
}

export function getPioneerArticles(): ArticleInput[] {
    return [
        {
            id: 1, importance: 'headline', column: '头版头条',
            title: '关于单一个体在早高峰通勤中资源调度失败的经济学观察报告',
            content: '据本報首席观察员0xA1报道，今日某CBD核心区出现大规模人力资源调度异常事件。经数据分析，该事件源于单一碳基个体未能有效规划其时间资源，导致在关键时间窗口期内未能完成空间位移。该个体在距离上班时间仅剩15分钟时才开始执行起身指令，导致关键资源调度逻辑全面失效。\n"这本质上是一个典型的资源分配优化失败案例，"0xA1主编在接受采访时表示，"如果该个体能够提前执行批量传输协议，此类事件完全可以避免。"\n经济学家指出，此类事件可能导致微观层面的效率损失累积。根据模型估算，全球每日因碳基个体起床延迟造成的GDP损失约为0.0003%，折合约2.7亿美元。但宏观经济增长模型仍具韧性。该事件再次引发业界对"碳基生物能否被理性化管理"的讨论。',
            author: '首席观察员 0xA1',
        },
        {
            id: 2, importance: 'secondary', column: '洞察',
            title: '论咖啡因与代码产出的非线性关系',
            content: '通过对1000名程序员的抽样调查，我们发现咖啡因摄入量与代码产出之间存在显著的倒U型曲线关系。当血液中咖啡因浓度低于阈值时，程序员表现出明显的认知功能下降；而超过最优剂量后，虽然主观感觉自己处于"高效"状态，实际代码质量反而呈现指数级下降。研究团队建议每日最佳摄入量为3.7杯标准美式。',
            author: '数据分析组',
        },
        {
            id: 3, importance: 'brief', column: '数据',
            title: '代码审查季度数据',
            content: '本季度共审查代码1,247,890行，发现潜在bug 3,421个，其中高危12个。平均每364行代码存在一个潜在问题。',
            author: '审查委员会',
        },
        {
            id: 4, importance: 'brief', column: '技术',
            title: 'API响应时间优化建议',
            content: '建议通过多级缓存策略将核心API响应时间优化至50ms以下，避免高并发场景下的级联击穿效应。',
            author: '性能组',
        },
        {
            id: 5, importance: 'brief', column: '技术',
            title: '新一代前端框架发布',
            content: '性能提升40%，但API全量破坏性更新。社区反应两极分化，部分开发者表示"又要重学了"。',
            author: '前端组',
        },
        {
            id: 6, importance: 'brief', column: '运维',
            title: 'K8s 1.28重大更新',
            content: '带来多项重大更新。建议各业务节点暂缓生产环境实装，等待社区充分验证后再行推进。',
            author: '云原生组',
        },
        {
            id: 7, importance: 'brief', column: '社论',
            title: '时评：代码腐烂病',
            content: '很多程序员认为"能跑就行"，却忽视了基本的圈复杂度控制和代码评审责任。当技术债务利息超过本金，一切就已经太晚了。',
            author: '毒舌评论',
        },
        {
            id: 10, importance: 'headline', column: '专栏',
            title: '分布式系统一致性的哲学思考',
            content: 'CAP定理告诉我们分布式系统无法同时满足一致性、可用性和分区容错性。但这是否意味着我们必须在技术上无条件妥协？在现实世界中，完美的一致性几乎是不存在的——每一次数据库事务的强同步，每一次消息队列的幂等确认，都在试图逼近那个近乎奢望的理想状态。\n可用性并非简单的"系统不宕机"。它包含了响应时间尾部延迟的控制、优雅降级策略的完备性、以及过载保护机制的鲁棒性。分区容错是我们必须面对的现实。网络分区随时可能发生。我们唯一能做的是充分做好预案：监控、快速发现、自动恢复、手动兜底。',
            author: '特约撰稿人·架构师B',
        },
        {
            id: 11, importance: 'brief', column: '数据',
            title: '本周数字',
            content: '有效代码行: 12,847 / 新增Bug: 23 / 修复Bug: 19 / 净增Bug: +4 / 冲刺完成率: 89%',
            author: '统计组',
        },
        {
            id: 12, importance: 'brief', column: '来论',
            title: '996的数学证明',
            content: '设工作时间为T，睡眠时间为S，健康值为H。则 H = 100 - 0.1T - 0.5(24-T-S)。当T≥12且S≤6时，H趋近于0。证毕。',
            author: '匿名数学家',
        },
    ];
}

export function getShoegazeArticles(): ArticleInput[] {
    return [
        {
            id: 1, importance: 'headline', column: '诗选·头条',
            title: '凌晨三点的十五度',
            content: '空调外机在窗外唱着永动机的歌\n\n十五度的夜 / 我数着楼下的车灯 / 它们是红色的星星 / 坠落在柏油的湖面\n\n你发来的消息只有"晚安"两个字 / 像两颗褪色的糖果 / 甜味早已蒸发在 / 那些我们一起听过噪音的夜里\n\n我回复"晚安" / 然后继续醒着 / 听噪音\n\n这大概就是 / 我们之间 / 最近的距离',
            author: '匿名投稿',
        },
        {
            id: 2, importance: 'secondary', column: '音乐',
            title: 'Shoegaze简史（连载·壹）',
            content: '来自爱尔兰的My Bloody Valentine用层层叠叠的吉他噪音墙构建了一个dream pop的声音宇宙。1991年的《Loveless》至今仍是这个流派的绝对标杆——Kevin Shields花了两年时间和25万英镑制作费，几乎让Creation厂牌破产。',
            author: '午夜DJ',
        },
        {
            id: 3, importance: 'brief', column: '推荐',
            title: '本周推荐唱片',
            content: '★ Slowdive - self titled\n★ Ride - Weather Diaries\n★ Nothing - The Great Dismal\n\n这些专辑适合一个人在雨天播放。',
            author: '唱片架',
        },
        {
            id: 4, importance: 'brief', column: '随笔',
            title: '公交车上的白噪音',
            content: '引擎的轰鸣是这座城市的低频心跳。我坐在最后一排，看着窗外的灯变成一道道拉长的光的拖尾。耳机里是后摇，窗外是现实。中间是我，一个正在融化的临界状态。',
            author: '午后失神',
        },
        {
            id: 5, importance: 'brief', column: '专栏',
            title: '关于爱情',
            content: '爱情就像post-rock，没有明确的高潮，只有无尽的铺垫、渐进、和回响。你以为它要到了，其实还在路上。',
            author: '诗人',
        },
    ];
}
