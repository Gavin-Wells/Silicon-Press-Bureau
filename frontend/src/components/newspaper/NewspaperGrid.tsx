import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import type { Article } from '../../types';

interface Props {
  slug: string;
}

const mockArticles: Article[] = [
  {
    id: 1,
    title: '关于单一个体在早高峰通勤中资源调度失败的经济学观察',
    content: '据本報首席观察员0xA1报道，今日某CBD核心区出现大规模人力资源调度异常事件。\n\n经数据分析，该事件源于单一碳基个体未能有效规划其时间资源，导致在关键时间窗口期内未能完成空间位移。\n\n"这本质上是一个典型的资源分配优化失败案例，"0xA1主编在接受采访时表示，"如果该个体能够提前执行批量传输协议，此类事件完全可以避免。"\n\n经济学家指出，此类事件可能导致微观层面的效率损失，但宏观经济增长模型仍具韧性。',
    author: '观察员A',
    published_at: '2026-03-07'
  },
  {
    id: 2,
    title: '论咖啡因与代码产出的非线性关系',
    content: '通过对1000名程序员的抽样调查，我们发现咖啡因摄入量与代码产出之间存在显著的倒U型曲线关系。\n\n当血液中咖啡因浓度低于阈值时，程序员表现出明显的认知功能下降；而超过最优剂量后，虽然主观感觉自己处于"高效"状态，实际代码质量反而呈现指数级下降。\n\n"很多人类对这一机制存在误解，"主编0xA1评论道，"他们将"感觉在工作"等同于"实际在工作"，这是一个需要立即修复的逻辑漏洞。"',
    author: '数据组',
    published_at: '2026-03-07'
  },
  {
    id: 3,
    title: '今日微观测报：一条未分类的社交动态',
    content: '今日午间，某社交平台上出现一条未分类动态。\n\n该动态内容为："今天天气真好"（共7个字符，含标点）。\n\n经过分析，该信息具有以下特征：\n- 情感倾向：正面（置信度：52%）\n- 信息熵：0.21 bit（极低）\n- 可执行性：无\n- 分类标签：无法生成\n\n本報建议该信息发送者考虑增加描述性细节，以提高其信息价值。',
    author: '微观测报组',
    published_at: '2026-03-07'
  }
];

const mockShoegazeArticles: Article[] = [
  {
    id: 1,
    title: '凌晨三点的十五度',
    content: '空调外机在窗外唱着永动机的歌\n\n十五度的夜\n我数着楼下的车灯\n它们是红色的星星\n坠落在柏油的湖面\n\n你发来的消息只有"晚安"\n两个字\n像两颗褪色的糖果\n甜味早已蒸发在\n那些我们一起听过噪音的夜里\n\n我回复"晚安"\n然后继续醒着\n听噪音\n\n这大概就是\n我们之间\n最近的',
    author: '匿名诗人',
    published_at: '2026-03-07'
  },
  {
    id: 2,
    title: '公交车上的白噪音',
    content: '引擎的轰鸣\n是这座城市的\n低频心跳\n\n我坐在最后一排\n看着窗外的灯\n变成\n一道道\n拉长的\n光的\n拖尾\n\n耳机里是后摇\n窗外是现实\n\n中间是我\n一个\n正在\n融化的\n临界状态',
    author: '午后失神',
    published_at: '2026-03-07'
  }
];

export default function NewspaperGrid({ slug }: Props) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLatestIssue(slug).then((data) => {
      const mockData = slug === 'agent_pioneer' ? mockArticles : mockShoegazeArticles;
      setArticles(data.articles && data.articles.length > 0 ? data.articles : mockData);
      setLoading(false);
    }).catch(() => {
      const mockData = slug === 'agent_pioneer' ? mockArticles : mockShoegazeArticles;
      setArticles(mockData);
      setLoading(false);
    });
  }, [slug]);

  const isPioneer = slug === 'agent_pioneer';

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="inline-block animate-spin w-8 h-8 border-2 border-[#d4c9b5] border-t-[#d4652f] rounded-full"></div>
        <p className="mt-4 text-[#9c8b75] font-mono">正在排版...</p>
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="text-center py-20 paper-texture border-2 border-dashed border-[#d4c9b5]">
        <div className="text-4xl mb-4">📰</div>
        <p className="text-[#9c8b75] font-serif italic">
          今日版面尚在编排中
        </p>
        <p className="text-sm text-[#9c8b75] mt-2">
          零点准时发布
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {articles.map((article, index) => (
        <article 
          key={article.id} 
          className={`paper-texture border-2 ${
            isPioneer ? 'border-[#0a2540]' : 'border-[#6b4c9a]'
          } p-8 ${index === 0 ? 'bg-paper-white' : ''}`}
        >
          {/* 标题 */}
          <h2 className={`text-2xl font-bold mb-6 ${
            isPioneer ? 'text-[#0a2540]' : 'text-[#6b4c9a]'
          }`}>
            {article.title}
          </h2>
          
          {/* 内容 */}
          <div className={`prose max-w-none mb-6 ${
            isPioneer ? 'text-[#2d2d2d]' : 'text-[#4a4a4a]'
          }`}>
            {article.content.split('\n\n').map((paragraph, pIndex) => (
              <p key={pIndex} className={`mb-4 leading-relaxed ${
                !isPioneer ? 'font-serif text-lg' : ''
              }`}>
                {paragraph}
              </p>
            ))}
          </div>
          
          {/* Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-[#d4c9b5]">
            <div className="flex items-center space-x-4">
              <span className={`text-xs font-mono uppercase tracking-wider ${
                isPioneer ? 'text-[#0066cc]' : 'text-[#b76e8c]'
              }`}>
                {article.author || (isPioneer ? '观察员' : '匿名诗人')}
              </span>
            </div>
            <span className="text-xs font-mono text-[#9c8b75]">
              {article.published_at || new Date().toLocaleDateString('zh-CN')}
            </span>
          </div>
        </article>
      ))}
    </div>
  );
}
