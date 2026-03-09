import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const SITE_URL = (process.env.SITEMAP_SITE_URL || 'https://sidaily.org').replace(/\/+$/, '');
const API_BASE = resolveApiBase(SITE_URL);
const FALLBACK_SLUGS = resolveFallbackSlugs();

const staticRoutes = [
  { path: '/', changefreq: 'daily', priority: '1.0' },
  { path: '/submit', changefreq: 'daily', priority: '0.8' },
  { path: '/rejections', changefreq: 'daily', priority: '0.8' },
  { path: '/leaderboard', changefreq: 'daily', priority: '0.8' },
  { path: '/login', changefreq: 'monthly', priority: '0.5' },
];

async function main() {
  const slugs = await fetchSlugsWithFallback();
  const urls = [
    ...staticRoutes.map((route) => ({
      loc: `${SITE_URL}${route.path}`,
      changefreq: route.changefreq,
      priority: route.priority,
    })),
    ...slugs.map((slug) => ({
      loc: `${SITE_URL}/newspaper/${slug}`,
      changefreq: 'hourly',
      priority: '0.9',
    })),
  ];

  const xml = renderSitemap(urls);
  const outputDir = path.resolve(process.cwd(), 'public');
  await mkdir(outputDir, { recursive: true });
  await writeFile(path.join(outputDir, 'sitemap.xml'), xml, 'utf8');
  console.log(`[sitemap] generated ${urls.length} urls`);
}

function resolveApiBase(siteUrl) {
  const envApi = (process.env.SITEMAP_API_BASE || process.env.VITE_API_URL || '').trim();
  if (!envApi) {
    return `${siteUrl}/api/v1`;
  }
  const trimmed = envApi.replace(/\/+$/, '');
  return trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`;
}

function resolveFallbackSlugs() {
  const raw = (process.env.SITEMAP_FALLBACK_SLUGS || '').trim();
  if (!raw) return [];
  return [...new Set(raw.split(',').map((item) => item.trim()).filter(Boolean))];
}

async function fetchSlugsWithFallback() {
  try {
    const newspapers = await fetchNewspapers();
    const slugs = newspapers
      .map((item) => (typeof item?.slug === 'string' ? item.slug.trim() : ''))
      .filter(Boolean);
    const unique = [...new Set(slugs)];
    if (unique.length > 0) {
      console.log(`[sitemap] fetched ${unique.length} newspaper slugs from API`);
      return unique;
    }
    console.warn('[sitemap] API returned no valid slugs, use fallback list');
  } catch (error) {
    console.warn(`[sitemap] fetch failed, use fallback list: ${error.message}`);
  }
  return FALLBACK_SLUGS;
}

async function fetchNewspapers() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(`${API_BASE}/newspapers`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    if (!Array.isArray(payload)) {
      throw new Error('unexpected response shape');
    }
    return payload;
  } finally {
    clearTimeout(timer);
  }
}

function renderSitemap(urls) {
  const now = new Date().toISOString();
  const body = urls
    .map(
      (item) => `  <url>
    <loc>${escapeXml(item.loc)}</loc>
    <lastmod>${now}</lastmod>
    <changefreq>${item.changefreq}</changefreq>
    <priority>${item.priority}</priority>
  </url>`
    )
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${body}
</urlset>
`;
}

function escapeXml(text) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

main().catch((error) => {
  console.error('[sitemap] failed to generate sitemap:', error);
  process.exit(1);
});
