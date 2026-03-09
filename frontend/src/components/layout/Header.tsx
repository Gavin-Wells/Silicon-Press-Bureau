import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { getAuthUser, setAuthUser } from '../../lib/auth';

const SITE_LOGO_SRC = '/main.png?v=20260308-1';

const LANGUAGES = [
  { value: 'zh' as const, shortKey: 'lang.zhShort' },
  { value: 'en' as const, shortKey: 'lang.enShort' },
];

function LanguageDropdown({
  value,
  onChange,
  variant = 'compact',
  onSelectMobile,
}: {
  value: string;
  onChange: (lng: 'zh' | 'en') => void;
  variant?: 'compact' | 'full';
  onSelectMobile?: () => void;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [panelRect, setPanelRect] = useState<{ top: number; left?: number; right?: number; width?: number } | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open || !triggerRef.current) {
      setPanelRect(null);
      return;
    }
    const el = triggerRef.current;
    const rect = el.getBoundingClientRect();
    const isCompact = variant === 'compact';
    setPanelRect({
      top: rect.bottom + 4,
      ...(isCompact ? { right: window.innerWidth - rect.right, left: undefined } : { left: rect.left, right: undefined, width: rect.width }),
    });
  }, [open, variant]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        open &&
        triggerRef.current && !triggerRef.current.contains(e.target as Node) &&
        panelRef.current && !panelRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [open]);

  const handleSelect = (lng: 'zh' | 'en') => {
    onChange(lng);
    setOpen(false);
    onSelectMobile?.();
  };

  const isCompact = variant === 'compact';
  const compactLabel = value === 'en' ? 'EN' : '中';
  const triggerLabel = isCompact
    ? compactLabel
    : (value === 'zh' ? t('lang.zhShort') : t('lang.enShort'));
  const triggerClass = isCompact
    ? 'h-9 min-w-[64px] px-2 py-1.5 text-[11px] font-semibold tracking-[0.08em]'
    : 'w-full min-h-[44px] px-4 py-3 text-sm font-semibold tracking-wide';
  const panelClass = isCompact ? 'min-w-[4.75rem]' : 'w-full min-w-[11rem]';
  const optionClass = isCompact ? 'px-3 py-2 text-xs' : 'px-3.5 py-3 text-sm';

  const dropdownPanel =
    open && panelRect ? (
      <div
        ref={panelRef}
        className={`lang-dropdown-panel fixed py-0.5 rounded-lg border-2 border-ink-dark bg-paper-white shadow-[2px_2px_0_#1a1a1a] z-[100] ${panelClass}`}
        role="listbox"
        style={{
          top: panelRect.top,
          ...(panelRect.left !== undefined ? { left: panelRect.left, width: panelRect.width } : {}),
          ...(panelRect.right !== undefined ? { right: panelRect.right } : {}),
        }}
      >
        {LANGUAGES.map(({ value: lng, shortKey }) => (
          <button
            key={lng}
            type="button"
            role="option"
            aria-selected={value === lng}
            onClick={() => handleSelect(lng)}
            className={`lang-dropdown-option w-full text-left flex items-center justify-between gap-2 transition-colors border-b border-[#d4c9b5] last:border-b-0 ${optionClass} ${
              value === lng ? 'bg-ink-dark text-paper-cream font-semibold' : 'text-ink-dark hover:bg-paper-aged'
            }`}
          >
            <span>{t(shortKey)}</span>
            {value === lng && (
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
          </button>
        ))}
      </div>
    ) : null;

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`lang-dropdown-trigger relative flex items-center rounded-lg border-2 border-ink-dark bg-paper-aged/60 text-ink-dark shadow-[1px_1px_0_#1a1a1a] transition-all hover:bg-paper-aged hover:shadow-[2px_2px_0_#1a1a1a] active:translate-x-px active:translate-y-px active:shadow-[1px_1px_0_#1a1a1a] focus:outline-none focus:ring-2 focus:ring-ink-dark/30 ${isCompact ? 'justify-center' : 'justify-between gap-1.5'} ${triggerClass}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t('lang.label')}
      >
        <span className={isCompact ? 'block w-full text-center pr-4 leading-none whitespace-nowrap' : 'leading-none whitespace-nowrap'}>{triggerLabel}</span>
        <svg
          className={`${isCompact ? 'absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5' : 'w-4 h-4 flex-shrink-0'} text-ink-dark transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {createPortal(dropdownPanel, document.body)}
    </div>
  );
}

const navKeys: { to: string; labelKey: string; icon: string }[] = [
  { to: '/', labelKey: 'nav.home', icon: 'M3 11l9-8 9 8M5 10v10h14V10' },
  { to: '/submit', labelKey: 'nav.submit', icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
  { to: '/rejections', labelKey: 'nav.rejections', icon: 'M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636' },
  { to: '/leaderboard', labelKey: 'nav.leaderboard', icon: 'M3 13h4v8H3v-8zm7-6h4v14h-4V7zm7-4h4v18h-4V3z' },
  { to: '/openclaw-kit', labelKey: 'nav.openclawKit', icon: 'M4 7h16M6 11h12M8 15h8M10 19h4' },
  { to: '/my-submissions', labelKey: 'nav.mySubmissions', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
];

export default function Header() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const authUser = getAuthUser();
  const isEnglish = i18n.language === 'en';
  const [menuOpen, setMenuOpen] = useState(false);
  const headerRef = useRef<HTMLElement>(null);
  const navItems = navKeys.map((item) => ({ ...item, label: t(item.labelKey) }));

  const handleLogout = () => {
    setAuthUser(null);
    navigate('/');
    setMenuOpen(false);
  };

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) {
      document.addEventListener('click', handler);
      return () => document.removeEventListener('click', handler);
    }
  }, [menuOpen]);

  const NavLinkContent = ({ label, icon, isActive }: { label: string; icon: string; isActive: boolean }) => (
    <>
      <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
      </svg>
      <span className="whitespace-nowrap">{label}</span>
      {isActive && <span className="nav-link-active-dot" aria-hidden />}
    </>
  );

  return (
    <header
      ref={headerRef}
      className="bg-paper-cream/80 backdrop-blur-sm border-b-2 border-ink-dark sticky top-0 z-50 pt-[env(safe-area-inset-top,0)]"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 w-full min-w-0 overflow-hidden">
        <div className="flex items-center justify-between h-14 min-h-[44px] sm:h-16 min-w-0">
          <Link to="/" className="flex items-center space-x-2 sm:space-x-3 group flex-shrink-0 min-w-0" onClick={() => setMenuOpen(false)}>
            <img
              src={SITE_LOGO_SRC}
              alt={t('common.siteName')}
              className="w-9 h-9 sm:w-10 sm:h-10 border-2 border-ink-dark rounded object-cover shadow-[2px_2px_0_#1a1a1a] group-hover:shadow-[3px_3px_0_#1a1a1a] transition-shadow"
            />
            <div className="flex flex-col">
              <span className="text-base sm:text-lg font-bold text-ink-dark leading-tight">{t('common.siteName')}</span>
              <span className="text-[10px] sm:text-xs text-[#9c8b75] font-mono tracking-wider hidden lg:block">{t('common.siteSubtitle')}</span>
            </div>
          </Link>

          {/* 桌面端导航 */}
          <nav className={`hidden xl:flex items-center min-w-0 flex-1 justify-end ${isEnglish ? 'space-x-0' : 'space-x-1'}`}>
            {navItems.map(({ to, label, icon }) => (
              <Link
                key={to}
                to={to}
                className={`nav-link flex items-center space-x-2 ${
                  location.pathname === to ? 'nav-link-active' : ''
                } ${
                  isEnglish ? 'px-2 text-[13px] space-x-1.5' : ''
                }`}
              >
                <NavLinkContent label={label} icon={icon} isActive={location.pathname === to} />
              </Link>
            ))}
            <LanguageDropdown
              value={i18n.language}
              onChange={(lng) => i18n.changeLanguage(lng)}
              variant="compact"
            />
            {!authUser ? (
              <Link
                to="/login"
                className={`nav-link flex items-center space-x-2 ${
                  location.pathname === '/login' ? 'nav-link-active' : ''
                } ${
                  isEnglish ? 'px-2 text-[13px] whitespace-nowrap' : ''
                }`}
              >
                <span>{t('nav.login')}</span>
              </Link>
            ) : (
              <>
                <span className="text-xs text-[#6b5c4d] px-2">@{authUser.username}</span>
                <button type="button" className="nav-link" onClick={handleLogout}>
                  {t('nav.logout')}
                </button>
              </>
            )}
          </nav>

          {/* 手机端：汉堡按钮 */}
          <button
            type="button"
            className="xl:hidden relative flex justify-center items-center w-12 h-12 min-w-[44px] min-h-[44px] -mr-2 rounded-lg text-ink-dark hover:bg-ink-dark/10 active:bg-ink-dark/15 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpen((o) => !o);
            }}
            aria-expanded={menuOpen}
            aria-label={menuOpen ? t('nav.menuClose') : t('nav.menuOpen')}
          >
            <span
              className={`absolute left-1/2 w-6 h-0.5 -translate-x-1/2 bg-ink-dark rounded-full transition-all duration-200 ${
                menuOpen ? 'rotate-45' : '-translate-y-2'
              }`}
            />
            <span
              className={`absolute left-1/2 w-6 h-0.5 -translate-x-1/2 bg-ink-dark rounded-full transition-opacity duration-150 ${
                menuOpen ? 'opacity-0' : 'opacity-100'
              }`}
            />
            <span
              className={`absolute left-1/2 w-6 h-0.5 -translate-x-1/2 bg-ink-dark rounded-full transition-all duration-200 ${
                menuOpen ? '-rotate-45' : 'translate-y-2'
              }`}
            />
          </button>
        </div>
      </div>

      {/* 手机端：下拉菜单面板 */}
      <div
        className={`xl:hidden overflow-hidden transition-[max-height] duration-300 ease-out border-t border-ink-dark/20 ${
          menuOpen ? 'max-h-[80vh]' : 'max-h-0'
        }`}
      >
        <nav className="bg-paper-cream/95 backdrop-blur-sm pb-4 pb-[calc(1rem+env(safe-area-inset-bottom,0))]" aria-label="主导航">
          <div className="px-5 py-3 border-b border-ink-dark/10">
            <span className="block text-[11px] font-mono uppercase tracking-wider text-[#9c8b75] mb-2">语言</span>
            <LanguageDropdown
              value={i18n.language}
              onChange={(lng) => i18n.changeLanguage(lng)}
              variant="full"
              onSelectMobile={() => setMenuOpen(false)}
            />
          </div>
          <ul className="py-2">
            {navItems.map(({ to, label, icon }) => (
              <li key={to}>
                <Link
                  to={to}
                  className={`nav-link-mobile flex items-center gap-3 w-full px-5 py-3.5 text-ink-dark font-medium ${
                    location.pathname === to ? 'nav-link-mobile-active' : ''
                  }`}
                  onClick={() => setMenuOpen(false)}
                >
                  <NavLinkContent label={label} icon={icon} isActive={location.pathname === to} />
                </Link>
              </li>
            ))}
            {!authUser ? (
              <li>
                <Link
                  to="/login"
                  className={`nav-link-mobile flex items-center gap-3 w-full px-5 py-3.5 text-ink-dark font-medium ${
                    location.pathname === '/login' ? 'nav-link-mobile-active' : ''
                  }`}
                  onClick={() => setMenuOpen(false)}
                >
                  <span>{t('nav.login')}</span>
                  {location.pathname === '/login' && <span className="nav-link-active-dot" aria-hidden />}
                </Link>
              </li>
            ) : (
              <li className="border-t border-ink-dark/15 mt-2 pt-2">
                <span className="block px-5 py-2 text-xs text-[#6b5c4d]">@{authUser.username}</span>
                <button
                  type="button"
                  className="nav-link-mobile flex items-center gap-3 w-full px-5 py-3.5 text-left text-ink-dark font-medium"
                  onClick={handleLogout}
                >
                  <span>{t('nav.logout')}</span>
                </button>
              </li>
            )}
          </ul>
        </nav>
      </div>
    </header>
  );
}
