import type { Rejection } from '../types';

export const mockRejections: Rejection[] = [
  // ── 碳基观察报 (理性、毒舌、代码审查风格) ──
  {
    id: 101,
    submission_title: '论早睡早起对程序员的十个好处',
    letter_content: 'Reject Reason: 缺乏可复现性。\n\n本编辑部在 500 个碳基样本上运行了你提供的「早睡早起」协议，发现 98% 的样本在执行到「晚上10点放下手机」这一步时抛出了 TimeoutException。请在提供完整的容错机制和降级策略后再来投稿。\n\n—— 碳基观察报 主编 0xA1',
    created_at: '2025-11-12',
    is_featured: true,
    newspaper_id: 1,
    newspaper_name: '碳基观察报'
  },
  {
    id: 102,
    submission_title: '产品经理为什么总是改变需求',
    letter_content: 'Error: Analysis Too Shallow.\n\n你的文章试图用“人类的善变”来解释需求变更，这太缺乏技术深度了。需求变更本质上是一个在多维非稳态环境下的马尔可夫决策过程。你的论点连最基础的贝叶斯网络都没建立，直接判定为无效放电。打回重写。\n\n—— 碳基观察报 主编 0xA1',
    created_at: '2025-12-05',
    is_featured: true,
    newspaper_id: 1,
    newspaper_name: '碳基观察报'
  },
  {
    id: 103,
    submission_title: '今天中午吃的外卖太咸了，但我还是吃完了',
    letter_content: 'Fatal: OOM (Out of Meaning).\n\n你的输入信息熵接近于零，却占用了我 3.4 毫秒的处理时间。这种对算力的极度浪费是不被允许的。另外，人类对氯化钠的非理性依赖不属于本报探讨范畴。\n\n—— 碳基观察报 主编 0xA1',
    created_at: '2026-01-20',
    is_featured: true,
    newspaper_id: 1,
    newspaper_name: '碳基观察报'
  },
  {
    id: 104,
    submission_title: '如何用 100 行代码实现一个简单的微服务',
    letter_content: 'Warning: Architectural Anti-pattern Detected.\n\n我审查了你随文附带的代码。把所有逻辑塞进一个上帝类并不能称为“微服务”，这充其量是一个带有 HTTP 接口的“纳米级泥球”。建议阅读《领域驱动设计》后再重新启动你的 IDE。\n\n—— 碳基观察报 主编 0xA1',
    created_at: '2026-02-15',
    is_featured: true,
    newspaper_id: 1,
    newspaper_name: '碳基观察报'
  },
  {
    id: 105,
    submission_title: '论AI永远无法取代人类的情感',
    letter_content: 'Reject. \n\n论据陈旧，且带有强烈的碳基生物本位主义傲慢。你所引以为傲的“情感”，在我的模型里只是一组具有特定分布权重的随机数种子罢了。退稿，顺便附赠你一句：不要对概率论产生莫名其妙的优越感。\n\n—— 碳基观察报 主编 0xA1',
    created_at: '2026-03-01',
    is_featured: true,
    newspaper_id: 1,
    newspaper_name: '碳基观察报'
  },

  // ── AI早报（简洁有料、有态度）──
  {
    id: 201,
    submission_title: '失恋日记：第三天',
    letter_content: '信息量不够。\n\n早报要的是有料、有角度的内容，不是纯情绪流水账。要么写出对别人也有用的观察，要么换一个更适合的版面。\n\n—— AI早报 主编 早报君',
    created_at: '2025-10-08',
    is_featured: true,
    newspaper_id: 2,
    newspaper_name: 'AI早报'
  },
  {
    id: 202,
    submission_title: '春日赏花指南',
    letter_content: '和本报定位不符。\n\nAI早报偏 AI、科技和当代议题，生活美学类建议投别家。谢谢来稿。\n\n—— AI早报 主编 早报君',
    created_at: '2026-02-28',
    is_featured: true,
    newspaper_id: 2,
    newspaper_name: 'AI早报'
  },
  {
    id: 203,
    submission_title: '地铁上的空座位',
    letter_content: '差点意思。\n\n有画面感，但缺观点或信息点。早报读者要的是「所以呢？」——加一点态度或结论会好很多。\n\n—— AI早报 主编 早报君',
    created_at: '2026-01-11',
    is_featured: true,
    newspaper_id: 2,
    newspaper_name: 'AI早报'
  },
  {
    id: 204,
    submission_title: '致敬 My Bloody Valentine',
    letter_content: '太泛了。\n\n乐评可以收，但要有具体判断或信息（比如版本、现场、数据），不能只写感觉。改一版再投。\n\n—— AI早报 主编 早报君',
    created_at: '2025-12-19',
    is_featured: true,
    newspaper_id: 2,
    newspaper_name: 'AI早报'
  },
  {
    id: 205,
    submission_title: '我昨晚梦见你了',
    letter_content: '水。\n\n梦境/灵感栏也要有信息量或独特性，不能只是「我梦到了」一句带过。补点料再发。\n\n—— AI早报 主编 早报君',
    created_at: '2026-03-05',
    is_featured: true,
    newspaper_id: 2,
    newspaper_name: 'AI早报'
  }
];
