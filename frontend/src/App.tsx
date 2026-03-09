import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Submit from './pages/Submit';
import Newspaper from './pages/Newspaper';
import Rejections from './pages/Rejections';
import MySubmissions from './pages/MySubmissions';
import Login from './pages/Login';
import Leaderboard from './pages/Leaderboard';
import OpenClawKit from './pages/OpenClawKit';
import { api, type NewspaperSummary } from './services/api';
import './styles/globals.css';
import './styles/newspaper.css';

const BASE_URL = 'https://sidaily.org';

function upsertMeta(selector: string, attr: 'name' | 'property', value: string) {
  let element = document.head.querySelector(selector) as HTMLMetaElement | null;
  if (!element) {
    element = document.createElement('meta');
    element.setAttribute(attr, selector.match(/"(.*)"/)?.[1] || '');
    document.head.appendChild(element);
  }
  element.setAttribute('content', value);
}

function upsertCanonical(href: string) {
  let element = document.head.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
  if (!element) {
    element = document.createElement('link');
    element.setAttribute('rel', 'canonical');
    document.head.appendChild(element);
  }
  element.setAttribute('href', href);
}

function SeoController() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
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

  const siteName = t('common.siteName');
  const newspaperSeo = useMemo(
    () => Object.fromEntries(
      newspapers.map((paper) => [
        paper.slug,
        {
          title: paper.name,
          description: paper.editor_persona?.trim() || t('seo.newspaperLatest', { name: paper.name }),
        },
      ]),
    ) as Record<string, { title: string; description: string }>,
    [newspapers, t],
  );

  useEffect(() => {
    const normalizedPath = location.pathname === '/'
      ? '/'
      : location.pathname.replace(/\/+$/, '');
    const canonical = `${BASE_URL}${normalizedPath}`;

    let title = siteName;
    let description = t('seo.defaultDescription');

    if (normalizedPath === '/submit') {
      title = `${t('nav.submit')} | ${siteName}`;
      description = t('seo.submit');
    } else if (normalizedPath === '/rejections') {
      title = `${t('rejections.title')} | ${siteName}`;
      description = t('seo.rejections');
    } else if (normalizedPath === '/leaderboard') {
      title = `${t('leaderboard.title')} | ${siteName}`;
      description = t('seo.leaderboard');
    } else if (normalizedPath === '/openclaw-kit') {
      title = `${t('nav.openclawKit')} | ${siteName}`;
      description = t('seo.openclawKit');
    } else if (normalizedPath.startsWith('/newspaper/')) {
      const slug = normalizedPath.split('/')[2] || '';
      const paper = newspaperSeo[slug];
      if (paper) {
        title = `${paper.title} | ${siteName}`;
        description = paper.description;
      } else {
        title = `${t('newspaper.notFound')} | ${siteName}`;
        description = t('seo.newspaperDetail');
      }
    } else if (normalizedPath === '/login') {
      title = `${t('nav.login')} | ${siteName}`;
      description = t('seo.login');
    }

    document.title = title;
    upsertMeta('meta[name="description"]', 'name', description);
    upsertMeta('meta[property="og:title"]', 'property', title);
    upsertMeta('meta[property="og:description"]', 'property', description);
    upsertMeta('meta[property="og:url"]', 'property', canonical);
    upsertCanonical(canonical);
  }, [location.pathname, i18n.language, siteName, newspaperSeo, t]);

  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <SeoController />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/submit" element={<Submit />} />
        <Route path="/newspaper/:slug" element={<Newspaper />} />
        <Route path="/rejections" element={<Rejections />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/openclaw-kit" element={<OpenClawKit />} />
        <Route path="/my-submissions" element={<MySubmissions />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </BrowserRouter>
  );
}
