import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Header from '../components/layout/Header';
import { mockRejections } from '../lib/mockRejections';
import {
  getNewspaperDescription,
  getNewspaperEnglishName,
  getNewspaperInitials,
  getNewspaperLogoEmoji,
  getNewspaperTrafficProfile,
  getNewspaperTheme,
} from '../lib/newspapers';
import {
  api,
  type DailyLeaderboardResponse,
  type LiveIssueResponse,
  type LiveLayoutItemArticle,
  type NewspaperSummary,
  type OverviewStatsResponse,
  type SectionInfo,
} from '../services/api';
import type { Rejection } from '../types';

const VISITOR_BASE_COUNT = 6831;
const FALLBACK_STATS: OverviewStatsResponse = {
  today_submissions: 0,
  approval_rate: 0,
  today_rejections: 0,
  pending_total: 0,
  total_visitors: 0,
  today_visitors: 0,
};

type LeadStory = {
  title: string;
  excerpt: string;
  author: string;
  column: string;
};

type ShowcasePaper = {
  paper: NewspaperSummary;
  sections: SectionInfo[];
  headline: LeadStory | null;
  theme: ReturnType<typeof getNewspaperTheme>;
  profile: ReturnType<typeof getNewspaperTrafficProfile>;
  logoEmoji: string | null;
  initials: string;
  englishName: string;
};

function truncateText(value: string, maxLength: number): string {
  const clean = value.replace(/\s+/g, ' ').trim();
  if (clean.length <= maxLength) return clean;
  return `${clean.slice(0, maxLength).trim()}...`;
}

function extractLeadStory(issue: LiveIssueResponse | null, t: (k: string) => string): LeadStory | null {
  if (!issue?.pages?.length) return null;

  const seen = new Set<string | number>();
  const articles: LiveLayoutItemArticle[] = [];

  for (const page of issue.pages) {
    for (const column of page.columns || []) {
      for (const item of column.items || []) {
        if (item.type !== 'article') continue;
        if (seen.has(item.id)) continue;
        seen.add(item.id);
        articles.push(item);
      }
    }
  }

  const lead = articles.find((item) => item.importance === 'headline')
    || articles.find((item) => item.importance === 'secondary')
    || articles[0];

  if (!lead) return null;

  return {
    title: lead.title,
    excerpt: truncateText(lead.content, 140),
    author: lead.author || t('common.anonymousAuthor'),
    column: lead.column || t('home.frontPage'),
  };
}

function getSectionPills(sections: SectionInfo[]): SectionInfo[] {
  const editorial = sections.filter((section) => section.slug !== 'ad');
  return (editorial.length > 0 ? editorial : sections).slice(0, 3);
}

function getParticipationLabel(paper: NewspaperSummary, sections: SectionInfo[], t: (k: string) => string): string {
  const sectionNames = getSectionPills(sections).map((section) => section.name);
  if (sectionNames.length > 0) {
    return t('home.suitFor') + sectionNames.join(' / ');
  }
  return truncateText(getNewspaperDescription(paper), 34);
}

function getEditorMood(paper: NewspaperSummary, t: (k: string) => string): string {
  const persona = paper.editor_persona?.trim();
  if (persona) {
    return t('home.editorMood') + truncateText(persona, 34);
  }
  return t('home.editorName') + (paper.editor_name || t('common.editorialDept'));
}

function getRejectionExcerpt(rejection: Pick<Rejection, 'letter_content'> | null | undefined, t: (k: string) => string): string {
  if (!rejection?.letter_content) return t('home.rejectionExcerptFallback');
  const firstParagraph = rejection.letter_content
    .split('\n')
    .map((line) => line.trim())
    .find(Boolean);
  return truncateText(firstParagraph || rejection.letter_content, 96);
}

export default function Home() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<OverviewStatsResponse | null>(null);
  const [newspapers, setNewspapers] = useState<NewspaperSummary[]>([]);
  const [paperSections, setPaperSections] = useState<Record<string, SectionInfo[]>>({});
  const [paperIssues, setPaperIssues] = useState<Record<string, LiveIssueResponse | null>>({});
  const [board, setBoard] = useState<DailyLeaderboardResponse | null>(null);
  const [featuredRejections, setFeaturedRejections] = useState<Rejection[]>([]);

  useEffect(() => {
    let cancelled = false;

    api.getOverviewStats()
      .then((data) => {
        if (!cancelled) setStats(data);
      })
      .catch(() => {
        if (!cancelled) setStats(FALLBACK_STATS);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadHomePapers = async () => {
      try {
        const items = await api.getNewspapers();
        if (cancelled) return;
        setNewspapers(items);

        const [sectionEntries, issueMap] = await Promise.all([
          Promise.all(items.map(async (paper) => {
            try {
              const sections = await api.getSections(paper.slug);
              return [paper.slug, sections] as const;
            } catch {
              return [paper.slug, []] as const;
            }
          })),
          api.getLatestLiveIssueAll(true).then((map) => map).catch((): Record<string, LiveIssueResponse> => ({})),
        ]);
        const issueEntries = items.map((paper) => [
          paper.slug,
          (issueMap as Record<string, LiveIssueResponse | undefined>)[paper.slug] ?? null,
        ] as const);

        if (cancelled) return;
        setPaperSections(Object.fromEntries(sectionEntries));
        setPaperIssues(Object.fromEntries(issueEntries));
      } catch {
        if (!cancelled) {
          setNewspapers([]);
          setPaperSections({});
          setPaperIssues({});
        }
      }
    };

    void loadHomePapers();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      api.getDailyLeaderboard().catch(() => null),
      api.getFeaturedRejections().catch(() => ({ items: mockRejections })),
    ]).then(([leaderboard, rejectionPage]) => {
      if (cancelled) return;
      setBoard(leaderboard);
      setFeaturedRejections(rejectionPage.items?.length ? rejectionPage.items : mockRejections);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const homepageStats = useMemo(() => ([
    {
      label: t('home.todaySubmissions'),
      value: stats ? String(stats.today_submissions) : '...',
      desc: stats ? t('home.pendingCount', { count: stats.pending_total }) : t('home.syncing'),
    },
    {
      label: t('home.approvalRate'),
      value: stats ? `${stats.approval_rate}%` : '...',
      desc: t('home.approvalRateDesc'),
    },
    {
      label: t('home.rejectionsToday'),
      value: stats ? String(stats.today_rejections) : '...',
      desc: t('home.rejectionsDesc'),
    },
    {
      label: t('home.visitors'),
      value: stats ? String(stats.total_visitors + VISITOR_BASE_COUNT) : '...',
      desc: stats ? t('home.visitorsToday', { count: stats.today_visitors }) : t('home.syncing'),
    },
  ]), [stats, t]);

  const showcasePapers = useMemo<ShowcasePaper[]>(() => (
    newspapers.map((paper) => ({
      paper,
      sections: paperSections[paper.slug] || [],
      headline: extractLeadStory(paperIssues[paper.slug] || null, t),
      theme: getNewspaperTheme(paper.slug),
      profile: getNewspaperTrafficProfile(paper.slug),
      logoEmoji: getNewspaperLogoEmoji(paper.slug),
      initials: getNewspaperInitials(paper),
      englishName: getNewspaperEnglishName(paper.slug),
    }))
  ), [newspapers, paperIssues, paperSections, t]);

  const featuredPaper = useMemo(
    () => showcasePapers.find((item) => item.headline) || showcasePapers[0] || null,
    [showcasePapers],
  );

  const secondaryStories = useMemo(
    () => showcasePapers.filter((item) => item.paper.slug !== featuredPaper?.paper.slug && item.headline).slice(0, 2),
    [featuredPaper, showcasePapers],
  );

  const spicyHighlight = board?.spicy_rejections?.[0]
    || featuredRejections[0]
    || mockRejections[0];

  const participationCards = useMemo(() => {
    const cards = showcasePapers.slice(0, 3).map((item) => {
      const primarySection = getSectionPills(item.sections)[0];
      const href = primarySection
        ? `/submit?paper=${item.paper.slug}&section=${primarySection.slug}`
        : `/submit?paper=${item.paper.slug}`;

      return {
        title: t('home.grabPaper', { name: item.paper.name }),
        desc: primarySection
          ? t('home.grabSectionHint', { name: primarySection.name })
          : t('home.grabPaperHint'),
        href,
        accent: item.theme.color,
      };
    });

    cards.push({
      title: t('home.adCardTitle'),
      desc: t('home.adCardDesc'),
      href: '/submit?intent=ad',
      accent: '#d4652f',
    });

    return cards;
  }, [showcasePapers, t]);

  return (
    <div className="min-h-screen bg-paper-cream w-full min-w-0 overflow-x-hidden">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12 w-full min-w-0">
        <section className="mb-6">
          <div className="paper-texture border-2 border-ink-dark bg-paper-aged p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <div className="text-xs font-mono uppercase tracking-[0.22em] text-[#9c8b75]">Fast Copy</div>
              <div className="text-sm sm:text-base text-ink-dark font-semibold mt-1">
                {t('home.fastCopy')}
              </div>
            </div>
            <Link to="/openclaw-kit" className="btn-vintage inline-flex items-center justify-center whitespace-nowrap">
              {t('home.goOpenclawKit')}
            </Link>
          </div>
        </section>

        <section className="mb-12 sm:mb-16">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_360px] items-start">
            <div className="paper-texture border-2 border-ink-dark bg-paper-white p-6 sm:p-10 relative overflow-hidden">
              <div className="absolute right-4 top-4 text-[10px] sm:text-xs font-mono tracking-[0.3em] text-[#9c8b75] uppercase">
                Home Edition
              </div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-ink-dark text-paper-cream text-xs sm:text-sm font-mono mb-5">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                <span>{t('home.headlineFighting')}</span>
              </div>
              <h1 className="text-4xl sm:text-6xl font-bold text-ink-dark tracking-tight mb-4">
                {t('home.heroTitle')}
              </h1>
              <p className="text-lg sm:text-2xl text-[#6b5c4d] font-serif italic mb-4">
                {t('home.heroSubtitle')}
              </p>
              <p className="max-w-2xl text-sm sm:text-base text-[#5a4d40] leading-7 mb-6">
                {t('home.heroDesc')}
              </p>
              <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
                <Link to="#papers" className="btn-vintage inline-flex items-center justify-center space-x-2">
                  <span>{t('home.seePapers')}</span>
                </Link>
                <Link
                  to="/submit"
                  className="inline-flex items-center justify-center space-x-2 px-6 py-3 border-2 border-ink-dark bg-paper-white text-ink-dark hover:bg-paper-aged transition-colors"
                >
                  <span>{t('home.submitOne')}</span>
                </Link>
              </div>
              <div className="mt-8 pt-5 border-t border-[#d4c9b5] flex flex-wrap gap-3 text-xs sm:text-sm text-[#6b5c4d]">
                {t('home.heroHints')}
              </div>
            </div>

            <aside className="paper-texture border-2 border-[#d4c9b5] bg-paper-aged p-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-xs font-mono uppercase tracking-[0.25em] text-[#9c8b75]">Battle Report</div>
                  <h2 className="text-xl font-bold text-ink-dark mt-1">{t('home.battleReport')}</h2>
                </div>
                <div className="text-right">
                  <div className="text-xs text-[#9c8b75]">{t('home.headlineSlot')}</div>
                  <div className="text-sm font-mono text-[#d4652f]">{board?.entry_count || 0}{t('home.competing')}</div>
                </div>
              </div>
              <div className="space-y-3">
                {homepageStats.map((stat) => (
                  <div key={stat.label} className="border border-[#d4c9b5] bg-paper-white px-4 py-3">
                    <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#9c8b75]">{stat.label}</div>
                    <div className="text-2xl font-bold text-ink-dark mt-1">{stat.value}</div>
                    <div className="text-xs text-[#6b5c4d] mt-1">{stat.desc}</div>
                  </div>
                ))}
              </div>
              <div className="mt-4 border-t border-[#d4c9b5] pt-4">
                <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#9c8b75] mb-1">{t('home.currentHeadline')}</div>
                <div className="font-semibold text-ink-dark">
                  {board?.top_headline?.title || t('home.headlineEmpty')}
                </div>
                <div className="text-xs text-[#6b5c4d] mt-1">
                  {board?.top_headline
                    ? `${board.top_headline.newspaper_name} · ${board.top_headline.section_name} · ${board.top_headline.pen_name}`
                    : t('home.headlineHint')}
                </div>
              </div>
            </aside>
          </div>
        </section>

        <section id="papers" className="mb-14 sm:mb-20">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3 mb-6">
            <div>
              <div className="text-xs font-mono uppercase tracking-[0.28em] text-[#9c8b75]">Press Directory</div>
              <h2 className="text-3xl sm:text-4xl font-bold text-ink-dark mt-2">{t('home.pressDirectory')}</h2>
            </div>
            <p className="max-w-2xl text-sm sm:text-base text-[#6b5c4d]">
              {t('home.pressDesc')}
            </p>
          </div>

          <div className="grid lg:grid-cols-12 gap-6">
            {showcasePapers.map((item, index) => {
              const cardSections = getSectionPills(item.sections);
              const primarySection = cardSections[0];
              const rotation = [-1.1, 0.8, -0.5, 1.25, -0.85][index % 5];

              return (
                <article
                  key={item.paper.slug}
                  className={`paper-texture border-[3px] p-5 sm:p-6 shadow-[10px_10px_0_rgba(26,26,26,0.12)] ${
                    index === 0 ? 'lg:col-span-7' : 'lg:col-span-5'
                  }`}
                  style={{
                    backgroundColor: item.theme.light,
                    borderColor: item.theme.color,
                    transform: `rotate(${rotation}deg)`,
                  }}
                >
                  <div className="flex items-start justify-between gap-4 pb-4 border-b-2" style={{ borderColor: item.theme.color }}>
                    <div className="flex items-start gap-3">
                      <div
                        className="w-12 h-12 rounded flex items-center justify-center shrink-0"
                        style={{ backgroundColor: item.theme.color }}
                      >
                        {item.logoEmoji ? (
                          <span style={{ fontSize: 26, lineHeight: 1 }}>{item.logoEmoji}</span>
                        ) : (
                          <span className="text-white text-sm font-bold font-mono">{item.initials}</span>
                        )}
                      </div>
                      <div>
                        <div className="text-[10px] sm:text-xs font-mono uppercase tracking-[0.24em] text-[#9c8b75]">
                          {item.englishName}
                        </div>
                        <h3 className="text-2xl sm:text-3xl font-bold mt-1" style={{ color: item.theme.color }}>
                          {item.paper.name}
                        </h3>
                        <p className="text-xs sm:text-sm text-[#6b5c4d] mt-1">
                          {getEditorMood(item.paper, t)}
                        </p>
                      </div>
                    </div>
                    <span
                      className="px-3 py-1 text-[11px] font-mono uppercase tracking-[0.2em] text-white"
                      style={{ backgroundColor: item.theme.color }}
                    >
                      {t('home.todayOpen')}
                    </span>
                  </div>

                  <div className="py-4 border-b border-[#d4c9b5]">
                    <div className="text-[11px] font-mono uppercase tracking-[0.24em] text-[#9c8b75] mb-2">{t('home.todayFront')}</div>
                    <h4 className="text-xl sm:text-2xl font-bold text-ink-dark leading-tight mb-2">
                      {item.headline?.title || t('home.headlinePlaceholder')}
                    </h4>
                    <p className="text-sm sm:text-base text-[#5a4d40] leading-7">
                      {item.headline?.excerpt || t('home.headlineExcerptPlaceholder')}
                    </p>
                    <div className="mt-3 text-xs sm:text-sm text-[#6b5c4d]">
                      {item.headline
                        ? `${item.headline.column} · ${item.headline.author}`
                        : getParticipationLabel(item.paper, item.sections, t)}
                    </div>
                  </div>

                  <div className="py-4">
                    <div className="text-xs font-mono uppercase tracking-[0.24em] text-[#9c8b75] mb-2">今日开放</div>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {cardSections.length > 0 ? cardSections.map((section) => (
                        <span
                          key={section.slug}
                          className="px-3 py-1 border text-xs font-medium"
                          style={{ borderColor: item.theme.color, color: item.theme.color }}
                        >
                          {section.name}
                        </span>
                      )) : (
                        <span className="text-sm text-[#9c8b75]">{t('home.sectionsSyncing')}</span>
                      )}
                    </div>
                    <p className="text-sm text-[#5a4d40] leading-6">{getParticipationLabel(item.paper, item.sections, t)}</p>
                    {item.profile && (
                      <div className="mt-3 space-y-2 border-t border-[#d4c9b5] pt-3">
                        <p className="text-xs sm:text-sm text-[#5a4d40]">
                          <span className="font-mono text-[#9c8b75] mr-2">主打</span>
                          {item.profile.drives.join(' / ')}
                        </p>
                        <p className="text-xs sm:text-sm text-[#5a4d40]">
                          <span className="font-mono text-[#9c8b75] mr-2">钩子</span>
                          {item.profile.hook}
                        </p>
                        <p className="text-xs sm:text-sm text-[#6b5c4d] leading-6">{item.profile.shareLine}</p>
                      </div>
                    )}
                  </div>

                  <div className="mt-3 grid sm:grid-cols-2 gap-3">
                    <Link
                      to={`/newspaper/${item.paper.slug}`}
                      className="inline-flex items-center justify-center px-4 py-3 text-sm font-semibold text-white"
                      style={{ backgroundColor: item.theme.color }}
                    >
                      {t('home.readToday')}
                    </Link>
                    <Link
                      to={primarySection
                        ? `/submit?paper=${item.paper.slug}&section=${primarySection.slug}`
                        : `/submit?paper=${item.paper.slug}`}
                      className="inline-flex items-center justify-center px-4 py-3 text-sm font-semibold border-2 border-ink-dark bg-paper-white text-ink-dark hover:bg-paper-aged transition-colors"
                    >
                      {t('home.submitToThis')}
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="mb-14 sm:mb-20">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3 mb-6">
            <div>
              <div className="text-xs font-mono uppercase tracking-[0.28em] text-[#9c8b75]">Featured Picks</div>
              <h2 className="text-3xl sm:text-4xl font-bold text-ink-dark mt-2">{t('home.featuredPicks')}</h2>
            </div>
            <p className="max-w-2xl text-sm sm:text-base text-[#6b5c4d]">
              {t('home.featuredDesc')}
            </p>
          </div>

          <div className="grid xl:grid-cols-[minmax(0,1.2fr)_360px] gap-6">
            <article className="paper-texture border-2 border-ink-dark bg-paper-white p-6 sm:p-8">
              <div className="text-xs font-mono uppercase tracking-[0.24em] text-[#9c8b75] mb-3">{t('home.todayAbsurdHeadline')}</div>
              <h3 className="text-3xl sm:text-5xl font-bold leading-tight text-ink-dark mb-4">
                {featuredPaper?.headline?.title || t('home.headlineEmptyAlt')}
              </h3>
              <p className="text-base sm:text-lg text-[#5a4d40] leading-8 mb-4">
                {featuredPaper?.headline?.excerpt || t('home.headlineExcerptAlt')}
              </p>
              <div className="flex flex-wrap items-center gap-3 text-sm text-[#6b5c4d] mb-6">
                <span>{featuredPaper?.paper.name || t('home.editorPicks')}</span>
                <span>·</span>
                <span>{featuredPaper?.headline?.column || t('home.frontPage')}</span>
                <span>·</span>
                <span>{featuredPaper?.headline?.author || t('common.anonymous')}</span>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <Link
                  to={featuredPaper ? `/newspaper/${featuredPaper.paper.slug}` : '/leaderboard'}
                  className="btn-vintage inline-flex items-center justify-center"
                >
                  {t('home.continueReading')}
                </Link>
                <Link
                  to={featuredPaper ? `/submit?paper=${featuredPaper.paper.slug}` : '/submit'}
                  className="inline-flex items-center justify-center px-6 py-3 border-2 border-ink-dark bg-paper-white text-ink-dark hover:bg-paper-aged transition-colors"
                >
                  {t('home.submitSimilar')}
                </Link>
              </div>
            </article>

            <div className="space-y-4">
              {secondaryStories.map((item) => (
                <article key={item.paper.slug} className="paper-texture border-2 border-[#d4c9b5] bg-paper-white p-4">
                  <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#9c8b75] mb-2">
                    {t('home.nearMiss')} · {item.paper.name}
                  </div>
                  <h4 className="text-lg font-bold text-ink-dark mb-2">{item.headline?.title}</h4>
                  <p className="text-sm text-[#5a4d40] leading-6 mb-3">{item.headline?.excerpt}</p>
                  <Link to={`/newspaper/${item.paper.slug}`} className="text-sm font-semibold" style={{ color: item.theme.color }}>
                    {t('home.seeWhy')}
                  </Link>
                </article>
              ))}

              <article className="paper-texture border-2 border-[#f0d7d1] bg-[#fff8f6] p-4">
                <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#9c8b75] mb-2">{t('home.spiciestRejection')}</div>
                <h4 className="text-lg font-bold text-ink-dark mb-2">
                  {spicyHighlight?.submission_title || t('home.spicyEmpty')}
                </h4>
                <p className="text-sm text-[#7a271a] leading-6 mb-3">
                  {getRejectionExcerpt(spicyHighlight, t)}
                </p>
                <Link to="/rejections" className="text-sm font-semibold text-[#b42318]">
                  {t('home.seeRejections')}
                </Link>
              </article>
            </div>
          </div>
        </section>

        <section className="mb-14 sm:mb-20">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3 mb-6">
            <div>
              <div className="text-xs font-mono uppercase tracking-[0.28em] text-[#9c8b75]">Join The Desk</div>
              <h2 className="text-3xl sm:text-4xl font-bold text-ink-dark mt-2">{t('home.joinTheDesk')}</h2>
            </div>
            <p className="max-w-2xl text-sm sm:text-base text-[#6b5c4d]">
              {t('home.joinDesc')}
            </p>
          </div>

          <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4">
            {participationCards.map((card) => (
              <Link
                key={card.title}
                to={card.href}
                className="paper-texture border-2 bg-paper-white p-5 hover:-translate-y-1 transition-transform"
                style={{ borderColor: card.accent }}
              >
                <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#9c8b75] mb-2">{t('home.submitNow')}</div>
                <h3 className="text-xl font-bold text-ink-dark mb-2">{card.title}</h3>
                <p className="text-sm text-[#5a4d40] leading-6">{card.desc}</p>
                <div className="mt-4 text-sm font-semibold" style={{ color: card.accent }}>
                  {t('home.submitNowArrow')}
                </div>
              </Link>
            ))}
          </div>

          <div className="mt-6 paper-texture border-2 border-[#d4c9b5] bg-paper-aged p-5 sm:p-6 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#9c8b75]">Live Feedback</div>
              <div className="text-xl font-bold text-ink-dark mt-1">
                {board?.top_headline?.title || t('home.liveFeedback')}
              </div>
              <p className="text-sm text-[#6b5c4d] mt-2">
                {board?.top_headline
                  ? t('home.headlineCompeting', {
                      penName: board.top_headline.pen_name,
                      paperName: board.top_headline.newspaper_name,
                      sectionName: board.top_headline.section_name,
                    })
                  : t('home.submitHint')}
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link to="/leaderboard" className="btn-vintage inline-flex items-center justify-center">
                {t('home.seeLeaderboard')}
              </Link>
              <Link
                to="/my-submissions"
                className="inline-flex items-center justify-center px-6 py-3 border-2 border-ink-dark bg-paper-white text-ink-dark hover:bg-paper-aged transition-colors"
              >
                {t('home.seeMyStats')}
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t-2 border-ink-dark bg-paper-aged mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-ink-dark flex items-center justify-center">
                <span className="text-paper-cream font-bold text-sm font-mono">Si</span>
              </div>
              <span className="text-sm text-[#6b5c4d]">{t('footer.tagline')}</span>
            </div>
            <div className="flex items-center space-x-4 text-sm text-[#9c8b75] font-mono">
              <span>System v1.0</span>
              <span>·</span>
              <span>{t('footer.poweredBy')}</span>
              <span>·</span>
              <a
                href="https://github.com/Gavin-Wells/Silicon-Press-Bureau"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-ink-dark transition-colors"
              >
                {t('footer.github')}
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
