import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api, type NewspaperSummary, type SectionInfo } from '../../services/api';
import { getAuthUser } from '../../lib/auth';
import {
  getNewspaperDescription,
  getNewspaperInitials,
  getNewspaperTagline,
  getNewspaperTheme,
} from '../../lib/newspapers';

export default function SubmitForm() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const adMode = searchParams.get('intent') === 'ad';
  const presetPaperSlug = searchParams.get('paper') || searchParams.get('newspaper') || '';
  const presetSectionSlug = searchParams.get('section') || '';
  const [newspapers, setNewspapers] = useState<NewspaperSummary[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [penName, setPenName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [newspaperSlug, setNewspaperSlug] = useState('');
  const [sectionSlug, setSectionSlug] = useState('');
  const [sections, setSections] = useState<SectionInfo[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState('');
  const [paperLoadError, setPaperLoadError] = useState('');
  const navigate = useNavigate();
  const authUser = getAuthUser();

  useEffect(() => {
    if (!authUser) return;
    if (!penName.trim() && authUser.pen_name) {
      setPenName(authUser.pen_name);
    }
    if (!contactEmail.trim() && authUser.email) {
      setContactEmail(authUser.email);
    }
  }, [authUser, penName, contactEmail]);

  useEffect(() => {
    let cancelled = false;

    api.getNewspapers()
      .then((items) => {
        if (cancelled) return;
        setNewspapers(items);
        setPaperLoadError('');
        setNewspaperSlug((current) => {
          if (presetPaperSlug && items.some((paper) => paper.slug === presetPaperSlug)) {
            return presetPaperSlug;
          }
          if (current && items.some((paper) => paper.slug === current)) return current;
          return items[0]?.slug || '';
        });
      })
      .catch((err: any) => {
        if (cancelled) return;
        setNewspapers([]);
        setPaperLoadError(err.message || t('submitForm.paperLoadError'));
      });

    return () => {
      cancelled = true;
    };
  }, [presetPaperSlug]);

  // 加载板块
  useEffect(() => {
    if (!newspaperSlug) {
      setSections([]);
      setSectionSlug('');
      return;
    }

    const loadSections = async () => {
      setSectionSlug('');
      setError('');
      try {
        const data = await api.getSections(newspaperSlug);
        setSections(data);
        if (adMode) {
          const adSection = data.find((section) => section.slug === 'ad');
          setSectionSlug(adSection?.slug || '');
          return;
        }
        if (presetSectionSlug && data.some((section) => section.slug === presetSectionSlug)) {
          setSectionSlug(presetSectionSlug);
          return;
        }
        setSectionSlug(data[0]?.slug || '');
      } catch (err: any) {
        setSections([]);
        setError(err.message || t('submitForm.sectionLoadError'));
      }
    };
    loadSections();
  }, [adMode, newspaperSlug, presetSectionSlug, t]);

  const selectedPaper = newspapers.find((p) => p.slug === newspaperSlug);
  const selectedTheme = getNewspaperTheme(selectedPaper?.slug);
  const selectedSection = sections.find(s => s.slug === sectionSlug);
  const isAdSection = selectedSection?.slug === 'ad';
  const visibleSections = adMode
    ? sections.filter((s) => s.slug === 'ad')
    : sections;

  // 字数展示（前端不再做限制，最终以服务端校验为准）
  const charCount = content.length;
  const charHint = selectedSection
    ? t('submitForm.charHint', { min: selectedSection.min_chars, max: selectedSection.max_chars })
    : '';
  const normalizedContactEmail = contactEmail.trim();
  const contactEmailValid =
    !normalizedContactEmail || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedContactEmail);

  const canSubmit = Boolean(
    newspapers.length > 0 &&
    title.trim() &&
    content.trim() &&
    sectionSlug &&
    contactEmailValid &&
    !isSubmitting,
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsSubmitting(true);
    setError('');

    try {
      await api.submitArticle({
        newspaper_slug: newspaperSlug,
        section_slug: sectionSlug,
        title: title.trim(),
        content: content.trim(),
        pen_name: penName.trim() || '匿名',
        contact_email: normalizedContactEmail || undefined,
      });
      setShowSuccess(true);
      setTimeout(() => navigate('/my-submissions'), 2500);
    } catch (err: any) {
      setError(err.message || t('submitForm.submitError'));
      setIsSubmitting(false);
    } finally {
    }
  };

  if (showSuccess) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="paper-texture border-2 border-ink-dark p-12 text-center animate-stamp">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center"
            style={{ backgroundColor: selectedTheme.color }}>
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-ink-dark mb-2">{t('submitForm.submitSuccess')}</h2>
          <p className="text-[#6b5c4d] mb-2">
            {t('submitForm.submitSuccessDesc', {
              type: isAdSection ? t('submitForm.typeAd') : t('submitForm.typeArticle'),
              paper: selectedPaper?.name ?? '',
              section: selectedSection?.name ?? '',
            })}
          </p>
          <p className="text-sm font-mono text-[#9c8b75]">
            {t('submitForm.reviewSoon')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="grid md:grid-cols-5 gap-8">
        {/* ── 左侧：报纸 + 板块选择 ── */}
        <div className="md:col-span-2 space-y-6">
          {paperLoadError && (
            <div className="p-3 rounded bg-red-50 border border-red-200 text-sm text-red-700">
              {paperLoadError}
            </div>
          )}

          <div>
            <h3 className="text-sm font-mono text-[#9c8b75] uppercase tracking-wider mb-3">
              {t('submitForm.selectPaper')}
            </h3>
            <div className="space-y-3">
              {newspapers.map((paper) => {
                const theme = getNewspaperTheme(paper.slug);
                return (
                  <button
                    key={paper.slug}
                    type="button"
                    onClick={() => setNewspaperSlug(paper.slug)}
                    className={`w-full p-4 rounded-lg border-2 transition-all text-left ${newspaperSlug === paper.slug
                        ? 'border-ink-dark shadow-[4px_4px_0_rgba(26,26,26,0.15)]'
                        : 'border-[#d4c9b5] hover:border-[#9c8b75]'
                      }`}
                  >
                    <div className="flex items-center space-x-3 mb-1">
                      <div className="w-8 h-8 rounded flex items-center justify-center"
                        style={{ backgroundColor: theme.color }}>
                        <span className="text-white font-bold text-xs">
                          {getNewspaperInitials(paper)}
                        </span>
                      </div>
                      <div>
                        <div className="font-semibold text-ink-dark">{paper.name}</div>
                        <div className="text-xs text-[#9c8b75]">{getNewspaperDescription(paper)}</div>
                      </div>
                    </div>
                    {newspaperSlug === paper.slug && (
                      <div className="mt-2 pt-2 border-t border-[#d4c9b5]">
                        <p className="text-xs italic" style={{ color: theme.accent }}>
                          "{getNewspaperTagline(paper)}"
                        </p>
                      </div>
                    )}
                  </button>
                );
              })}
              {newspapers.length === 0 && !paperLoadError && (
                <div className="p-3 rounded border border-[#d4c9b5] bg-[#f8f4ec] text-sm text-[#6b5c4d]">
                  {t('submitForm.noPapers')}
                </div>
              )}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-mono text-[#9c8b75] uppercase tracking-wider mb-3">
              {adMode ? t('submitForm.selectAdSection') : t('submitForm.selectSection')}
            </h3>
            <div className="space-y-2">
              {visibleSections.map((sec) => (
                <button
                  key={sec.slug}
                  type="button"
                  onClick={() => setSectionSlug(sec.slug)}
                  className={`w-full p-3 rounded border text-left transition-all ${sectionSlug === sec.slug
                      ? 'border-ink-dark bg-[#f0ebe0] shadow-sm'
                      : 'border-[#d4c9b5] hover:border-[#9c8b75] hover:bg-[#f8f4ec]'
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-semibold text-sm ${sectionSlug === sec.slug ? 'text-ink-dark' : 'text-[#6b5c4d]'
                      }`}>
                      {sec.name}
                    </span>
                    <span className="text-[10px] font-mono text-[#9c8b75]">
                      {sec.min_chars}-{sec.max_chars}{t('common.chars')}
                    </span>
                  </div>
                  <p className="text-xs text-[#9c8b75] mt-1">{sec.description}</p>
                </button>
              ))}
            </div>
            {adMode && visibleSections.length === 0 && (
              <div className="p-3 rounded border border-[#d4c9b5] bg-[#f8f4ec] text-sm text-[#6b5c4d]">
                {t('submitForm.noAdSection')}
              </div>
            )}

            {/* 评分维度提示 */}
            {selectedSection && selectedSection.scoring_dimensions?.length > 0 && (
              <div className="mt-3 p-3 rounded bg-[#f8f4ec] border border-[#e8e0d0]">
                <p className="text-xs font-mono text-[#9c8b75] mb-2">{t('submitForm.scoringDims')}</p>
                <div className="space-y-1">
                  {selectedSection.scoring_dimensions.map((d) => (
                    <div key={d.name} className="flex items-center justify-between text-xs">
                      <span className="text-[#6b5c4d]">{d.name}</span>
                      <div className="flex items-center gap-1">
                        <div className="w-16 h-1.5 bg-[#e8e0d0] rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${d.weight * 100}%`,
                              backgroundColor: selectedTheme.accent,
                            }}
                          ></div>
                        </div>
                        <span className="text-[#9c8b75] font-mono w-8 text-right">
                          {Math.round(d.weight * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── 右侧：表单 ── */}
        <div className="md:col-span-3">
          <form onSubmit={handleSubmit} className="space-y-6">
            {adMode && (
              <div className="paper-texture border-2 border-[#d4652f] bg-[#fff7ef] p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-ink-dark">{t('submitForm.adBannerTitle')}</p>
                    <p className="text-sm text-[#6b5c4d]">{t('submitForm.adBannerDesc')}</p>
                  </div>
                  <button
                    type="button"
                    className="text-xs font-mono text-[#9c8b75] hover:text-ink-dark"
                    onClick={() => navigate('/submit')}
                  >
                    {t('submitForm.switchToNormalBtn')}
                  </button>
                </div>
              </div>
            )}

            {/* 标题 + 笔名 + 联系邮箱 */}
            <div className="paper-texture border-2 border-ink-dark p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-[#d4652f]"></div>
                  <span className="text-sm font-mono text-[#6b5c4d]">{isAdSection ? t('submitForm.newAd') : t('submitForm.newArticle')}</span>
                </div>
                <span className="text-xs font-mono text-[#9c8b75]">
                  {new Date().toLocaleDateString('zh-CN', {
                    year: 'numeric', month: 'long', day: 'numeric'
                  })}
                </span>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink-dark mb-2">{isAdSection ? t('submitForm.adTitleLabel') : t('submitForm.titleLabel')}</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="input-vintage"
                    placeholder={isAdSection ? t('submitForm.adTitlePlaceholder') : t('submitForm.titlePlaceholder')}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink-dark mb-2">
                    {t('submitForm.penNameLabel')} <span className="font-normal text-[#9c8b75]">{t('submitForm.penNameHint')}</span>
                  </label>
                  <input
                    type="text"
                    value={penName}
                    onChange={(e) => setPenName(e.target.value)}
                    className="input-vintage"
                    placeholder={t('submitForm.penNamePlaceholder')}
                    maxLength={50}
                  />
                  {authUser && (
                    <p className="text-xs text-[#9c8b75] mt-1">
                      {t('submitForm.loggedInHint', { username: authUser.username })}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink-dark mb-2">
                    {t('submitForm.emailLabel')} <span className="font-normal text-[#9c8b75]">{t('submitForm.emailHint')}</span>
                  </label>
                  <input
                    type="email"
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    className="input-vintage"
                    placeholder={t('login.emailPlaceholder')}
                    maxLength={320}
                  />
                  {!contactEmailValid && (
                    <p className="text-xs text-red-600 mt-1">{t('submitForm.emailInvalid')}</p>
                  )}
                </div>
              </div>
            </div>

            {/* 正文 */}
            <div className="paper-texture border-2 border-ink-dark p-6 min-h-[300px]">
              <label className="block text-sm font-semibold text-ink-dark mb-2">{isAdSection ? t('submitForm.adContentLabel') : t('submitForm.contentLabel')}</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full h-[250px] bg-transparent border-none focus:outline-none resize-none text-ink-dark leading-relaxed font-serif"
                placeholder={selectedSection
                  ? isAdSection
                    ? t('submitForm.adContentPlaceholder', { name: selectedSection.name, min: selectedSection.min_chars, max: selectedSection.max_chars })
                    : t('submitForm.contentPlaceholder', { name: selectedSection.name, min: selectedSection.min_chars, max: selectedSection.max_chars })
                  : adMode ? t('submitForm.selectPaperFirstAd') : t('submitForm.selectSectionFirst')
                }
                required
              />
              <div className="flex justify-between items-center mt-4 pt-4 border-t border-[#d4c9b5]">
                <span className="text-xs font-mono text-[#9c8b75]">
                  {charCount} {t('common.chars')}
                  {charHint && ` / ${charHint}`}
                </span>
              </div>
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="p-3 rounded bg-red-50 border border-red-200 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* 提交按钮 */}
            <button
              type="submit"
              disabled={!canSubmit}
              className="btn-vintage w-full flex items-center justify-center space-x-3 py-4 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>{t('submitForm.submitting')}</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span>
                    {!newspaperSlug ? t('submitForm.noPaper') : !sectionSlug ? t('submitForm.selectSectionFirstBtn') : isAdSection ? t('submitForm.submitAdBtn') : t('submitForm.submitBtn')}
                  </span>
                </>
              )}
            </button>

            <div className="flex items-start space-x-2 p-4 bg-paper-aged rounded border border-[#d4c9b5]">
              <svg className="w-5 h-5 text-[#d4652f] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm text-[#6b5c4d]">
                <p className="font-medium mb-1">{t('submitForm.noticeTitle')}</p>
                <ul className="text-xs space-y-1 text-[#9c8b75]">
                  <li>· {isAdSection ? t('submitForm.noticeAd1') : t('submitForm.notice1')}</li>
                  <li>· {isAdSection ? t('submitForm.noticeAd2') : t('submitForm.notice2')}</li>
                  <li>· {t('submitForm.notice3')}</li>
                  <li>· {t('submitForm.notice4')}</li>
                </ul>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
