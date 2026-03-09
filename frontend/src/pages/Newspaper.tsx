import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, Link } from 'react-router-dom';
import { api, type LiveIssueResponse, type LiveLayoutItem, type LiveLayoutPage, type NewspaperSummary } from '../services/api';
import { mockRejections } from '../lib/mockRejections';
import { getAuthUser } from '../lib/auth';
import { downloadShareCard } from '../lib/shareCard';
import {
  getNewspaperEnglishName,
  getNewspaperLogoEmoji,
  getNewspaperTagline,
  getNewspaperTheme,
} from '../lib/newspapers';


/* ──────────────── 主组件 ──────────────── */
export default function Newspaper() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const authUser = getAuthUser();
  const isLoggedInUser = Boolean(authUser?.username);
  const [newspapers, setNewspapers] = useState<NewspaperSummary[]>([]);
  const [papersLoaded, setPapersLoaded] = useState(false);

  const [currentSpread, setCurrentSpread] = useState(0);
  const [isSinglePageMode, setIsSinglePageMode] = useState(false);
  const [selectedIssueDate, setSelectedIssueDate] = useState('');
  const [autoFlip, setAutoFlip] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [liveIssue, setLiveIssue] = useState<LiveIssueResponse | null>(null);
  const [controlsHeight, setControlsHeight] = useState(62);
  const controlsRef = useRef<HTMLDivElement | null>(null);
  const shareCardRef = useRef<HTMLElement | null>(null);
  const [isSharing, setIsSharing] = useState(false);

  const [rejections, setRejections] = useState<any[]>([]);

  useEffect(() => {
    let cancelled = false;
    api.getNewspapers()
      .then((items) => {
        if (!cancelled) {
          setNewspapers(items);
          setPapersLoaded(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setNewspapers([]);
          setPapersLoaded(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // 切换报纸时回到第一页
  useEffect(() => {
    setCurrentSpread(0);
    setSelectedIssueDate('');
  }, [slug]);

  const toDateInput = (d: Date) => {
    const y = d.getFullYear();
    const m = `${d.getMonth() + 1}`.padStart(2, '0');
    const day = `${d.getDate()}`.padStart(2, '0');
    return `${y}-${m}-${day}`;
  };

  const todayStr = toDateInput(new Date());
  const isArchiveMode = Boolean(selectedIssueDate);

  // 加载精选退稿（作为空白页彩蛋）
  useEffect(() => {
    api.getFeaturedRejections()
      .then(data => setRejections(data?.items && data.items.length > 0 ? data.items : mockRejections))
      .catch(() => setRejections(mockRejections));
  }, []);

  useEffect(() => {
    if (!slug) return;
    let timer: number | undefined;

    const fetchLiveIssue = async (isInitial = false) => {
      try {
        if (isInitial) {
          setLoading(true);
        }
        const data = selectedIssueDate
          ? await api.getIssueByDate(slug, selectedIssueDate)
          : (isLoggedInUser && authUser?.username
              ? await api.getLatestLiveIssueForAdmin(slug, authUser.username)
              : await api.getLatestLiveIssue(slug));
        setLiveIssue(data);
        setError('');
      } catch {
        if (selectedIssueDate) {
          setError(t('newspaper.dateNotFound', { date: selectedIssueDate }));
        } else {
          setError(t('newspaper.serviceError'));
        }
      } finally {
        if (isInitial) {
          setLoading(false);
        }
      }
    };

    fetchLiveIssue(true);
    if (!selectedIssueDate) {
      timer = window.setInterval(() => fetchLiveIssue(false), 10000);
    }
    return () => {
      if (timer) {
        window.clearInterval(timer);
      }
    };
  }, [slug, selectedIssueDate, t]);

  useEffect(() => {
    const onFsChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener('fullscreenchange', onFsChange);
    return () => document.removeEventListener('fullscreenchange', onFsChange);
  }, []);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(max-width: 800px)');
    const handleChange = (event: MediaQueryList | MediaQueryListEvent) => {
      setIsSinglePageMode(event.matches);
    };
    handleChange(mediaQuery);
    const listener = (event: MediaQueryListEvent) => handleChange(event);
    mediaQuery.addEventListener('change', listener);
    return () => mediaQuery.removeEventListener('change', listener);
  }, []);

  const pages: LiveLayoutPage[] = useMemo(() => {
    if (!liveIssue) return [];
    return liveIssue.pages || [];
  }, [liveIssue]);

  const currentPaper = newspapers.find((paper) => paper.slug === slug);
  const paperName = currentPaper?.name || liveIssue?.issue_meta?.newspaper_name || '硅基印务局';
  const paperEditor = currentPaper?.editor_name || '编辑部';
  const paperTagline = getNewspaperTagline(currentPaper);
  const paperNameEn = getNewspaperEnglishName(slug);
  const paperTheme = getNewspaperTheme(slug);
  const paperRedTitle = paperTheme.redTitle;
  const paperLogoEmoji = getNewspaperLogoEmoji(slug);

  // ── 对开计算 ──
  const totalSpreads = Math.max(1, Math.ceil(pages.length / 2));
  const totalViews = isSinglePageMode ? Math.max(1, pages.length) : totalSpreads;
  const leftPageIndex = isSinglePageMode ? currentSpread : currentSpread * 2;
  const rightPageIndex = isSinglePageMode ? currentSpread : currentSpread * 2 + 1;
  const leftPage = pages[leftPageIndex];
  const rightPage = isSinglePageMode ? undefined : pages[rightPageIndex]; // 可能 undefined
  const shareSections = useMemo(() => {
    const seen = new Set<string>();
    const names: string[] = [];
    for (const page of pages) {
      const sectionName = (page.section_name || '').trim();
      if (!sectionName || seen.has(sectionName)) continue;
      seen.add(sectionName);
      names.push(sectionName);
      if (names.length >= 3) break;
    }
    return names;
  }, [pages]);
  const shareHeadline = useMemo(() => {
    const seen = new Set<string | number>();
    const candidates: (LiveLayoutItem & { type: 'article' })[] = [];
    for (const page of pages) {
      for (const column of page.columns || []) {
        for (const item of column.items || []) {
          if (item.type !== 'article') continue;
          if (seen.has(item.id)) continue;
          seen.add(item.id);
          candidates.push(item as LiveLayoutItem & { type: 'article' });
        }
      }
    }
    return candidates.find((item) => item.importance === 'headline')
      || candidates.find((item) => item.importance === 'secondary')
      || candidates[0]
      || null;
  }, [pages]);

  useEffect(() => {
    setCurrentSpread((prev) => Math.min(prev, Math.max(0, totalViews - 1)));
  }, [totalViews]);

  useEffect(() => {
    if (!autoFlip) return;
    const timer = window.setInterval(() => {
      setCurrentSpread((prev) => {
        if (prev >= totalViews - 1) return 0;
        return prev + 1;
      });
    }, 8000);
    return () => window.clearInterval(timer);
  }, [autoFlip, totalViews]);

  useEffect(() => {
    const controlsElement = controlsRef.current;
    if (!controlsElement) return;

    const updateControlsHeight = () => {
      const measured = Math.ceil(controlsElement.getBoundingClientRect().height);
      setControlsHeight((prev) => (prev === measured ? prev : measured));
    };

    updateControlsHeight();

    const observer = new ResizeObserver(() => updateControlsHeight());
    observer.observe(controlsElement);
    window.addEventListener('resize', updateControlsHeight);

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', updateControlsHeight);
    };
  }, []);

  if (!slug || (papersLoaded && newspapers.length > 0 && !currentPaper)) {
    return (
      <div className="np-wrapper">
        <div style={{ textAlign: 'center', paddingTop: '20vh', fontFamily: '"Noto Serif SC", serif' }}>
          <div style={{ fontSize: 72, fontWeight: 900, color: '#333' }}>404</div>
          <p style={{ fontSize: 18, color: '#666', marginTop: 16 }}>{t('newspaper.notFound')}</p>
          <Link to="/" style={{ color: '#888', fontSize: 14, marginTop: 24, display: 'inline-block' }}>{t('common.backToHome')}</Link>
        </div>
      </div>
    );
  }

  const issueDate = liveIssue?.issue_meta?.issue_date ? new Date(liveIssue.issue_meta.issue_date) : new Date();
  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
  const dateStr = `${issueDate.getFullYear()}年${issueDate.getMonth() + 1}月${issueDate.getDate()}日  星期${weekDays[issueDate.getDay()]}`;
  const lunarDate = '乙巳年 二月初八';
  const issueNum = liveIssue?.issue_meta?.issue_number ?? '--';

  /* ──── 从 page 中提取去重后的文章列表 ──── */
  const getPageArticles = (page: LiveLayoutPage) => {
    const seen = new Set<string | number>();
    const articles: LiveLayoutItem[] = [];
    for (const col of page.columns) {
      for (const item of col.items) {
        if (item.type !== 'article') continue;
        const aid = item.id;
        if (seen.has(aid)) continue;
        seen.add(aid);
        articles.push(item);
      }
    }
    return articles;
  };

  /* ──── 渲染单篇文章 ──── */
  const renderArticle = (item: LiveLayoutItem & { type: 'article' }) => {
    const isAdArticle = (item.column || '').includes('广告');
    const cls = item.importance === 'headline' ? 'np-cell-headline'
      : item.importance === 'secondary' ? 'np-cell-secondary'
      : 'np-cell-brief';

    return (
      <div
        key={`article-${item.id}`}
        className={`np-cell ${cls} ${isAdArticle ? 'np-cell-ad' : ''}`}
      >
        {isAdArticle && <div className="np-ad-badge">{t('newspaper.adBadge')}</div>}
        <div className="np-column-label">{item.column}</div>
        <h3 className={`np-headline ${
          item.importance === 'headline' ? 'np-headline-1'
          : item.importance === 'secondary' ? 'np-headline-2'
          : 'np-headline-3'
        }`}>
          {item.title}
        </h3>
        <div className="np-byline">{item.author}</div>
        <div className={`np-body ${item.importance === 'headline' ? 'np-body-cols' : ''}`}>
          {item.content.split('\n').map((para, i) => (
            <p key={i}>{para}</p>
          ))}
        </div>
      </div>
    );
  };

  /* ──── 渲染单页 ──── */
  const renderPage = (page: LiveLayoutPage | undefined, pageIndex: number) => {
    if (!page) {
      // 只在“完全没有版面内容”时展示退稿彩蛋；
      // 一旦已有任意版面内容，缺页只显示普通留白，避免干扰阅读。
      if (pages.length > 0) {
        return (
          <div className="np-paper np-paper-empty">
            <div className="np-empty-wrap">
              <div className="np-empty-topline">
                <span>{t('newspaper.issueEnd')}</span>
                <span>{paperName}</span>
              </div>
              <h2 className="np-empty-title">{t('newspaper.layoutEnd')}</h2>
              <div className="np-empty-grid">
                <div className="np-empty-card">
                  <div className="np-empty-card-body">{t('newspaper.readLeft')}</div>
                </div>
              </div>
              <div className="np-empty-footer">{t('newspaper.thanks')}</div>
            </div>
          </div>
        );
      }

      const pending = liveIssue?.status === 'pending_publish';
      
      // 取出属于当前报纸的退稿记录，如果不够就拿所有的凑数
      let pool = rejections.filter(r => r.newspaper_name === paperName);
      if (pool.length < 2) pool = rejections;
      
      // 随机/分页展示 2 条退稿记录
      const safeIndex = (pageIndex * 2) % (pool.length || 1);
      const items = pool.slice(safeIndex, safeIndex + 2);

      return (
        <div className="np-paper np-paper-empty">
          <div className="np-empty-wrap">
            <div className="np-empty-topline">
              <span>{pending ? t('newspaper.editing') : t('newspaper.supplement')}</span>
              <span>{paperName}</span>
            </div>
            <h2 className="np-empty-title">
              {t('newspaper.rejectionShow')}
            </h2>
            <div className="np-empty-grid">
              {items.length > 0 ? items.map((r, idx) => (
                <div key={idx} className="np-empty-card">
                  <div className="np-empty-card-title">被毙稿件：《{r.submission_title}》</div>
                  <div className="np-empty-card-body np-reject-body">
                    {r.letter_content}
                  </div>
                </div>
              )) : (
                <div className="np-empty-card">
                  <div className="np-empty-card-body">{t('newspaper.archiving')}</div>
                </div>
              )}
            </div>
            <div className="np-empty-footer">
              {pending ? t('newspaper.pendingFooter') : t('newspaper.rejectionFooter')}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="np-paper">
        {/* ──── 报头 (头版独有) ──── */}
        {pageIndex === 0 && (
          <div className="np-masthead">
            <div className="np-masthead-top">
              <span>第 {issueNum} 期（总第 {issueNum} 期）</span>
              <span>{dateStr}</span>
              <span>{lunarDate}</span>
            </div>
            <div className="np-masthead-name-row">
              <div className="np-masthead-left-deco">
                <span className="np-masthead-price">每份定价：免费</span>
                <span className="np-masthead-sub">AI驱动·每日自动发行</span>
              </div>
              <h1 className={`np-masthead-name ${paperRedTitle ? 'np-masthead-name-red' : ''}`}>
                {paperLogoEmoji && (
                  <span
                    style={{
                      display: 'inline-block',
                      marginRight: '0.15em',
                      verticalAlign: 'middle',
                      fontSize: '0.75em',
                      lineHeight: 1,
                    }}
                    aria-hidden="true"
                  >
                    {paperLogoEmoji}
                  </span>
                )}
                {paperName}
              </h1>
              <div className="np-masthead-right-deco">
                <span className="np-masthead-slogan">"{paperTagline}"</span>
                <span className="np-masthead-editor">主编 / {paperEditor}</span>
              </div>
            </div>
            <div className="np-masthead-en">
              {paperLogoEmoji && (
                <span style={{ marginRight: '0.4em' }} aria-hidden="true">{paperLogoEmoji}</span>
              )}
              {paperNameEn}
              {paperLogoEmoji && (
                <span style={{ marginLeft: '0.4em' }} aria-hidden="true">{paperLogoEmoji}</span>
              )}
            </div>
            <div className="np-masthead-rules">
              <div className="np-rule-thick"></div>
              <div className="np-rule-thin"></div>
            </div>
          </div>
        )}

        {/* ──── 非头版页眉 ──── */}
        {pageIndex !== 0 && (
          <div className="np-page-header">
            <span className="np-ph-left">{issueNum}期 · {dateStr}</span>
            <span className="np-ph-center">{paperName}</span>
            <span className="np-ph-right">第 {page.page_num} 版 · {page.section_name}</span>
          </div>
        )}

        {/* ──── 版面标签 ──── */}
        {pageIndex === 0 && (
          <div className="np-section-label">
            <span>第 {page.page_num} 版</span>
            <span className="np-section-label-name">{page.section_name}</span>
          </div>
        )}

        {/* ──── 内容区（CSS Grid 按重要性自动分区） ──── */}
        <div className="np-content">
          <div className="np-grid">
            {getPageArticles(page).map((item) =>
              item.type === 'article' ? renderArticle(item as any) : null
            )}
          </div>
        </div>

        {/* ──── 版脚 ──── */}
        <div className="np-footer">
          <span>硅基印务局 出品</span>
          <span>Powered by Tensorout · © 2026 · <a href="https://github.com/Gavin-Wells/Silicon-Press-Bureau" target="_blank" rel="noopener noreferrer" className="np-footer-link">GitHub</a></span>
          <span>第 {page.page_num} 版 / 共 {pages.length} 版</span>
        </div>
      </div>
    );
  };

  const toggleFullscreen = async () => {
    const root = document.documentElement;
    if (!document.fullscreenElement) {
      await root.requestFullscreen();
      return;
    }
    await document.exitFullscreen();
  };

  const shiftIssueDate = (deltaDays: number) => {
    const baseDateStr = selectedIssueDate || liveIssue?.issue_meta?.issue_date || todayStr;
    const base = new Date(`${baseDateStr}T00:00:00`);
    base.setDate(base.getDate() + deltaDays);
    const next = toDateInput(base);
    if (next > todayStr) return;
    setCurrentSpread(0);
    setSelectedIssueDate(next);
  };

  const generateSharePoster = async () => {
    if (!shareCardRef.current || !slug) return;

    const issueDateForShare = selectedIssueDate || liveIssue?.issue_meta?.issue_date || todayStr;
    const deepLink = new URL(window.location.href);
    if (selectedIssueDate) {
      deepLink.searchParams.set('date', selectedIssueDate);
    } else {
      deepLink.searchParams.delete('date');
    }

    setIsSharing(true);
    try {
      await downloadShareCard({
        element: shareCardRef.current,
        deepLink: deepLink.toString(),
        filename: `${slug}-${issueDateForShare}-share.png`,
        qrCaption: t('newspaper.shareScanHint'),
        footerTitle: `${paperName} · ${t('newspaper.shareDatePrefix')} ${issueDateForShare}`,
        footerMeta: 'Silicon Press Bureau',
      });

      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(deepLink.toString()).catch(() => undefined);
      }
    } catch {
      window.alert(t('newspaper.shareFailed'));
    } finally {
      setIsSharing(false);
    }
  };

  return (
    <div
      className="np-wrapper"
      style={{ '--np-controls-height': `${controlsHeight}px` } as CSSProperties}
    >
      {loading && (
        <div className="np-loading-overlay">
          <p>{t('newspaper.loading')}</p>
        </div>
      )}
      {!loading && error && (
        <div className="np-status-banner np-status-banner-error" role="status" aria-live="polite">
          <span>{error}</span>
          <span className="np-status-banner-sub">{t('newspaper.errorSub')}</span>
        </div>
      )}
      {!loading && !error && liveIssue?.status === 'pending_publish' && (
        <div className="np-status-banner" role="status" aria-live="polite">
          <span>{isArchiveMode ? t('newspaper.notPublished') : t('newspaper.editingToday')}</span>
          <span className="np-status-banner-sub">
            {isArchiveMode ? t('newspaper.editingHint') : t('newspaper.publishTime')}
          </span>
        </div>
      )}

      {/* ======== 双页对开主体 ======== */}
      <div className="np-spread">
        {renderPage(leftPage, leftPageIndex)}
        {!isSinglePageMode && renderPage(rightPage, rightPageIndex)}
      </div>

      {/* ======== 浮动控制条 ======== */}
      <div className="np-controls" ref={controlsRef}>
        <div className="np-ctrl-group np-ctrl-submit-actions">
          <Link to="/submit" className="np-submit-action np-ctrl-submit-action np-submit-action-primary">
            {t('newspaper.submitArticle')}
          </Link>
          <Link to="/submit?intent=ad" className="np-submit-action np-ctrl-submit-action np-submit-action-ad">
            {t('newspaper.submitAd')}
          </Link>
        </div>
        <Link to="/" className="np-ctrl-back">{t('newspaper.backToBureau')}</Link>
        <div className="np-ctrl-group">
          <span className="np-ctrl-label">第{issueNum}期</span>
          <span className="np-ctrl-label">{dateStr}</span>
        </div>
        <div className="np-ctrl-group np-ctrl-archive">
          <button
            onClick={() => shiftIssueDate(-1)}
            className="np-ctrl-btn"
            title={t('newspaper.prevDay')}
          >{t('newspaper.prevDay')}</button>
          <input
            type="date"
            value={selectedIssueDate}
            max={todayStr}
            onChange={(e) => {
              setCurrentSpread(0);
              setSelectedIssueDate(e.target.value);
            }}
            className="np-ctrl-date"
            aria-label="选择往期日期"
          />
          <button
            onClick={() => shiftIssueDate(1)}
            className="np-ctrl-btn"
            disabled={!selectedIssueDate}
            title={t('newspaper.nextDay')}
          >{t('newspaper.nextDay')}</button>
          <button
            onClick={() => {
              setCurrentSpread(0);
              setSelectedIssueDate('');
            }}
            className="np-ctrl-btn"
            disabled={!selectedIssueDate}
            title={t('newspaper.backToLatest')}
          >{t('newspaper.backToLatest')}</button>
        </div>
        <div className="np-ctrl-group">
          <button
            onClick={() => setCurrentSpread(Math.max(0, currentSpread - 1))}
            disabled={currentSpread === 0}
            className="np-ctrl-btn"
          >◂</button>
          <span className="np-ctrl-label">
            {isSinglePageMode
              ? `${leftPageIndex + 1}版`
              : `${leftPageIndex + 1}-${Math.min(rightPageIndex + 1, pages.length)}版`}
          </span>
          <button
            onClick={() => setCurrentSpread(Math.min(totalViews - 1, currentSpread + 1))}
            disabled={currentSpread >= totalViews - 1}
            className="np-ctrl-btn"
          >▸</button>
        </div>
        <div className="np-ctrl-group">
          <button
            onClick={generateSharePoster}
            className="np-ctrl-btn"
            disabled={isSharing || loading || Boolean(error)}
          >
            {isSharing ? t('newspaper.sharing') : t('newspaper.share')}
          </button>
          <button
            onClick={() => setAutoFlip((v) => !v)}
            className="np-ctrl-btn"
          >
            {autoFlip ? t('newspaper.pauseFlip') : t('newspaper.autoFlip')}
          </button>
          <button
            onClick={toggleFullscreen}
            className="np-ctrl-btn"
          >
            {isFullscreen ? t('newspaper.exitFullscreen') : t('newspaper.fullscreen')}
          </button>
        </div>
      </div>

      <div style={{ position: 'fixed', left: '-10000px', top: 0, width: 760, pointerEvents: 'none', zIndex: -1 }}>
        <article
          ref={shareCardRef}
          className="paper-texture border-[3px] p-6 shadow-[10px_10px_0_rgba(26,26,26,0.12)]"
          style={{
            backgroundColor: paperTheme.light,
            borderColor: paperTheme.color,
            transform: 'none',
          }}
        >
          <div className="flex items-start justify-between gap-4 pb-4 border-b-2" style={{ borderColor: paperTheme.color }}>
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 rounded flex items-center justify-center shrink-0" style={{ backgroundColor: paperTheme.color }}>
                {paperLogoEmoji ? (
                  <span style={{ fontSize: 26, lineHeight: 1, transform: 'translateY(-2px)' }}>{paperLogoEmoji}</span>
                ) : (
                  <span className="text-white text-sm leading-none font-bold font-mono" style={{ transform: 'translateY(-2px)' }}>{paperName.slice(0, 1)}</span>
                )}
              </div>
              <div>
                <div className="text-xs font-mono uppercase tracking-[0.24em] text-[#9c8b75]">{paperNameEn}</div>
                <h3 className="text-3xl font-bold mt-1" style={{ color: paperTheme.color }}>{paperName}</h3>
                <p className="text-sm text-[#6b5c4d] mt-1">{t('newspaper.shareDatePrefix')} {selectedIssueDate || liveIssue?.issue_meta?.issue_date || todayStr}</p>
              </div>
            </div>
            <span className="inline-flex items-center justify-center px-3 py-2 min-h-[30px] text-[11px] leading-none font-mono uppercase tracking-[0.2em] text-white" style={{ backgroundColor: paperTheme.color }}>
              <span style={{ transform: 'translateY(-2px)' }}>{t('home.todayOpen')}</span>
            </span>
          </div>

          <div className="py-4 border-b border-[#d4c9b5]">
            <div className="text-[11px] font-mono uppercase tracking-[0.24em] text-[#9c8b75] mb-2">{t('home.todayFront')}</div>
            <h4 className="text-2xl font-bold text-ink-dark leading-tight mb-2">{shareHeadline?.title || t('home.headlinePlaceholder')}</h4>
            <p className="text-base text-[#5a4d40] leading-7">{shareHeadline?.content ? `${shareHeadline.content.slice(0, 130).trim()}...` : t('home.headlineExcerptPlaceholder')}</p>
            <div className="mt-3 text-sm text-[#6b5c4d]">{shareHeadline ? `${shareHeadline.column} · ${shareHeadline.author}` : t('home.frontPage')}</div>
          </div>

          <div className="py-4">
            <div className="text-xs font-mono uppercase tracking-[0.24em] text-[#9c8b75] mb-2">{t('home.todayOpen')}</div>
            <div className="flex flex-wrap gap-2 mb-3">
              {(shareSections.length ? shareSections : [t('home.frontPage')]).map((sectionName) => (
                <span key={sectionName} className="inline-flex items-center px-3 py-1 border text-xs leading-none font-medium" style={{ borderColor: paperTheme.color, color: paperTheme.color }}>
                  <span style={{ transform: 'translateY(-2px)' }}>{sectionName}</span>
                </span>
              ))}
            </div>
            <p className="text-sm text-[#5a4d40] leading-6">{paperTagline}</p>
          </div>
        </article>
      </div>
    </div>
  );
}
