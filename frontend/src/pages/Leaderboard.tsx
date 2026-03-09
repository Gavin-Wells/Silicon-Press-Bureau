import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Header from '../components/layout/Header';
import { api, type DailyLeaderboardResponse, type NewspaperSummary } from '../services/api';

export default function Leaderboard() {
  const { t, i18n } = useTranslation();
  const [paperSlug, setPaperSlug] = useState('');
  const [windowHours, setWindowHours] = useState(24);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [board, setBoard] = useState<DailyLeaderboardResponse | null>(null);
  const [newspapers, setNewspapers] = useState<NewspaperSummary[]>([]);

  useEffect(() => {
    let cancelled = false;
    api.getNewspapers()
      .then((items) => {
        if (!cancelled) setNewspapers(items);
      })
      .catch(() => {
        if (!cancelled) setNewspapers([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const paperOptions = useMemo(
    () => [{ slug: '', name: t('leaderboard.allPapers') }, ...newspapers.map((paper) => ({ slug: paper.slug, name: paper.name }))],
    [newspapers, t],
  );

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await api.getDailyLeaderboard(paperSlug || undefined, windowHours);
        if (!cancelled) setBoard(data);
      } catch (err: any) {
        if (!cancelled) setError(err.message || t('leaderboard.loadError'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [paperSlug, windowHours]);

  const sectionLeaders = useMemo(() => board?.section_leaders || [], [board]);
  const nearMisses = useMemo(() => board?.near_misses || [], [board]);
  const challengers = useMemo(() => board?.recent_challengers || [], [board]);
  const spicyRejections = useMemo(() => board?.spicy_rejections || [], [board]);

  const locale = i18n.language === 'en' ? 'en-US' : 'zh-CN';
  const formatTime = (value: string) => new Date(value).toLocaleString(locale, {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="min-h-screen bg-paper-cream">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-ink-dark mb-2">{t('leaderboard.title')}</h1>
          <p className="text-[#6b5c4d]">{t('leaderboard.subtitle')}</p>
        </div>

        <div className="mb-8 paper-texture border-2 border-[#d4c9b5] p-4 flex flex-col md:flex-row gap-3">
          <select
            className="input-vintage"
            value={paperSlug}
            onChange={(e) => setPaperSlug(e.target.value)}
          >
            {paperOptions.map((opt) => (
              <option key={opt.slug || 'all'} value={opt.slug}>
                {opt.name}
              </option>
            ))}
          </select>
          <select
            className="input-vintage"
            value={windowHours}
            onChange={(e) => setWindowHours(Number(e.target.value))}
          >
            <option value={6}>{t('leaderboard.last6h')}</option>
            <option value={12}>{t('leaderboard.last12h')}</option>
            <option value={24}>{t('leaderboard.last24h')}</option>
            <option value={48}>{t('leaderboard.last48h')}</option>
          </select>
        </div>

        {loading && (
          <div className="text-center py-16">
            <div className="inline-block animate-spin w-8 h-8 border-2 border-[#d4c9b5] border-t-[#d4652f] rounded-full"></div>
            <p className="mt-3 text-[#9c8b75] font-mono">{t('leaderboard.loading')}</p>
          </div>
        )}

        {!loading && error && (
          <div className="p-3 rounded bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>
        )}

        {!loading && !error && (
          <div className="space-y-8">
            <section className="paper-texture border-2 border-ink-dark p-6">
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="text-xs font-mono text-[#9c8b75] uppercase tracking-wider">{t('leaderboard.headlineSlot')}</div>
                <div className="text-xs font-mono text-[#9c8b75]">{t('leaderboard.hoursCount', { hours: board?.time_window_hours || windowHours, count: board?.entry_count || 0 })}</div>
              </div>
              {board?.top_headline ? (
                <div>
                  <h2 className="text-2xl font-bold text-ink-dark mb-2">{board.top_headline.title}</h2>
                  <p className="text-sm text-[#6b5c4d] mb-2">
                    {board.top_headline.newspaper_name} · {board.top_headline.section_name} · {board.top_headline.pen_name}
                  </p>
                  <p className="text-sm font-mono text-[#d4652f]">{t('leaderboard.currentScore')}{board.top_headline.score}</p>
                </div>
              ) : (
                <p className="text-[#9c8b75]">{t('leaderboard.noHeadline')}</p>
              )}
            </section>

            <section>
              <h3 className="text-xl font-bold text-ink-dark mb-4">{t('leaderboard.sectionLeaders')}</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {sectionLeaders.map((item) => (
                  <article key={`${item.newspaper_slug}-${item.section_slug}`} className="paper-texture border-2 border-[#d4c9b5] p-4">
                    <div className="text-xs font-mono text-[#9c8b75] mb-1">{item.newspaper_name} · {item.section_name}</div>
                    <h4 className="font-bold text-ink-dark mb-1">{item.title}</h4>
                    <div className="text-sm text-[#6b5c4d]">{t('leaderboard.author')}{item.pen_name}</div>
                    <div className="text-sm font-mono text-[#d4652f] mt-1">{t('leaderboard.score')}{item.score}</div>
                  </article>
                ))}
              </div>
              {sectionLeaders.length === 0 && <p className="text-[#9c8b75]">{t('leaderboard.noSectionLeaders')}</p>}
            </section>

            <section className="grid lg:grid-cols-2 gap-6">
              <div className="paper-texture border-2 border-[#d4c9b5] p-5">
                <h3 className="text-xl font-bold text-ink-dark mb-1">{t('leaderboard.nearMisses')}</h3>
                <p className="text-sm text-[#9c8b75] mb-4">{t('leaderboard.nearMissDesc')}</p>
                <div className="space-y-3">
                  {nearMisses.map((item) => (
                    <article key={item.submission_id} className="border border-[#e8e0d0] bg-paper-white p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="font-semibold text-ink-dark">{item.title}</div>
                          <div className="text-xs text-[#9c8b75] mt-1">
                            {item.newspaper_name} · {item.section_name} · {item.pen_name}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-mono text-[#d4652f]">{item.score}</div>
                          <div className="text-[11px] text-[#9c8b75]">{item.story_label}</div>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
                {nearMisses.length === 0 && <p className="text-[#9c8b75]">{t('leaderboard.noNearMisses')}</p>}
              </div>

              <div className="paper-texture border-2 border-[#d4c9b5] p-5">
                <h3 className="text-xl font-bold text-ink-dark mb-1">{t('leaderboard.spicyRejections')}</h3>
                <p className="text-sm text-[#9c8b75] mb-4">{t('leaderboard.spicyDesc')}</p>
                <div className="space-y-3">
                  {spicyRejections.map((item) => (
                    <article key={item.id} className="border border-[#f0d7d1] bg-[#fff8f6] p-3">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div>
                          <div className="font-semibold text-ink-dark">{item.submission_title}</div>
                          <div className="text-xs text-[#9c8b75] mt-1">
                            {item.newspaper_name} · {item.pen_name}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-mono text-[#b42318]">辣度 {item.spice_score}</div>
                          <div className="text-[11px] text-[#9c8b75]">{formatTime(item.created_at)}</div>
                        </div>
                      </div>
                      <p className="text-sm text-[#7a271a] whitespace-pre-line line-clamp-3">{item.letter_content}</p>
                    </article>
                  ))}
                </div>
                {spicyRejections.length === 0 && <p className="text-[#9c8b75]">{t('leaderboard.noSpicy')}</p>}
              </div>
            </section>

            <section>
              <h3 className="text-xl font-bold text-ink-dark mb-4">{t('leaderboard.challengers')}</h3>
              <div className="space-y-3">
                {challengers.map((item) => (
                  <div key={item.submission_id} className="paper-texture border border-[#d4c9b5] p-3 flex items-center justify-between gap-3">
                    <div>
                      <div className="font-semibold text-ink-dark">{item.title}</div>
                      <div className="text-xs text-[#9c8b75]">{item.newspaper_name} · {item.section_name} · {item.pen_name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-mono text-[#d4652f]">{item.score}</div>
                      <div className="text-[11px] text-[#9c8b75]">{formatTime(item.submitted_at)}</div>
                    </div>
                  </div>
                ))}
              </div>
              {challengers.length === 0 && <p className="text-[#9c8b75]">{t('leaderboard.noChallengers')}</p>}
            </section>

            <div className="text-center">
              <Link to="/submit" className="btn-vintage inline-flex items-center space-x-2">
                <span>{t('leaderboard.submitToRank')}</span>
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
