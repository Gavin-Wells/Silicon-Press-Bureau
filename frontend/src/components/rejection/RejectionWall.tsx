import { useEffect, useState } from 'react';
import { api, type NewspaperSummary } from '../../services/api';
import type { Rejection } from '../../types';
import { mockRejections } from '../../lib/mockRejections';
import { formatShanghaiDate } from '../../lib/datetime';
import { getNewspaperTheme, resolvePaperSlug } from '../../lib/newspapers';

const PAGE_SIZE = 12;

export default function RejectionWall() {
  const [rejections, setRejections] = useState<Rejection[]>([]);
  const [newspapers, setNewspapers] = useState<NewspaperSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [pageLoading, setPageLoading] = useState(false);
  const [transitioning, setTransitioning] = useState(false);

  const loadPage = async (nextPage: number) => {
    setPageLoading(true);
    setTransitioning(true);
    try {
      const data = await api.getFeaturedRejections(nextPage, PAGE_SIZE);
      const rows = data.items.length > 0 ? data.items : mockRejections;
      // 延后一帧更新，避免换页瞬间闪烁
      requestAnimationFrame(() => {
        setRejections(rows);
        setPage(data.page || nextPage);
        setHasMore(Boolean(data.has_more) && data.items.length > 0);
        setTotal(data.total || rows.length);
      });
    } catch {
      setRejections(mockRejections);
      setPage(1);
      setHasMore(false);
      setTotal(mockRejections.length);
    } finally {
      setPageLoading(false);
      window.setTimeout(() => setTransitioning(false), 140);
    }
  };

  useEffect(() => {
    api.getNewspapers()
      .then((items) => setNewspapers(items))
      .catch(() => setNewspapers([]));

    loadPage(1).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="inline-block animate-spin w-8 h-8 border-2 border-[#d4c9b5] border-t-[#d4652f] rounded-full"></div>
        <p className="mt-4 text-[#9c8b75] font-mono">正在调取退稿记录...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className={`space-y-6 transition-opacity duration-200 ${transitioning ? 'opacity-70' : 'opacity-100'}`}>
      {rejections.map((r, index) => {
        const paperSlug = resolvePaperSlug(r, newspapers);
        const theme = getNewspaperTheme(paperSlug);
        
        return (
          <div 
            key={r.id}
            className="relative group"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            {/* 装饰性别针 */}
            <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 z-10">
              <div className="w-4 h-4 rounded-full shadow-md" style={{ backgroundColor: theme.color }}></div>
            </div>
            
            {/* 信纸 */}
            <div
              className="paper-texture border-2 p-6 transform rotate-[-0.5deg] group-hover:rotate-0 transition-transform duration-300"
              style={{ borderColor: theme.color }}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4 pb-4 border-b border-[#d4c9b5]">
                <div>
                  <div className="text-xs font-mono text-[#9c8b75] uppercase tracking-wider mb-1">
                    原始稿件
                  </div>
                  <div className="text-sm font-semibold text-ink-dark line-through">
                    {r.submission_title}
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  <span className={`status-rejected`}>
                    REJECTED
                  </span>
                  <span className="text-xs font-mono text-[#9c8b75] mt-1">
                    {r.newspaper_name}
                  </span>
                </div>
              </div>
              
              {/* Rejection Letter Content */}
              <div
                className="mb-4 p-4 border-l-4"
                style={{ backgroundColor: theme.light, borderLeftColor: theme.accent }}
              >
                <p className="text-sm text-[#1a1a1a] leading-relaxed whitespace-pre-wrap font-serif">
                  {r.letter_content}
                </p>
              </div>
              
              {/* Footer */}
              <div className="flex items-center justify-between text-xs font-mono text-[#9c8b75]">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: theme.accent }}></span>
                  <span>{r.newspaper_name}</span>
                </div>
                <span>{formatShanghaiDate(r.created_at)}</span>
              </div>
            </div>
          </div>
        );
      })}
      </div>
      
      {/* Empty State */}
      {rejections.length === 0 && (
        <div className="text-center py-20 paper-texture border-2 border-dashed border-[#d4c9b5]">
          <div className="text-4xl mb-4">📭</div>
          <p className="text-[#9c8b75] font-serif italic">
            暂无退稿记录
          </p>
          <p className="text-sm text-[#9c8b75] mt-2">
            成为第一个"幸运儿"吧
          </p>
        </div>
      )}

      {rejections.length > 0 && (
        <div className="flex items-center justify-between pt-2 text-sm font-mono text-[#9c8b75]">
          <span>第 {page} 页 · 共 {Math.max(1, Math.ceil(total / PAGE_SIZE))} 页</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="btn-vintage px-3 py-1 disabled:opacity-50"
              disabled={pageLoading || page <= 1}
              onClick={() => loadPage(page - 1)}
            >
              上一页
            </button>
            <button
              type="button"
              className="btn-vintage px-3 py-1 disabled:opacity-50"
              disabled={pageLoading || !hasMore}
              onClick={() => loadPage(page + 1)}
            >
              {pageLoading ? '加载中...' : '下一页'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
