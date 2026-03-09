import type { NewspaperSummary } from '../services/api';
import type { Rejection } from '../types';

type NewspaperTheme = {
  color: string;
  accent: string;
  light: string;
  redTitle: boolean;
};

export type NewspaperTrafficProfile = {
  drives: string[];
  pitch: string;
  hook: string;
  shareLine: string;
};

const THEMES: NewspaperTheme[] = [
  { color: '#0a2540', accent: '#0066cc', light: '#e8f0f8', redTitle: true },
  { color: '#6b4c9a', accent: '#b76e8c', light: '#e8dff0', redTitle: false },
  { color: '#8a1538', accent: '#f97316', light: '#fbe7dc', redTitle: true },
  { color: '#1f4d3a', accent: '#2f9e67', light: '#e6f4ec', redTitle: false },
  { color: '#5b3a29', accent: '#c97b36', light: '#f7eadf', redTitle: true },
];

const SLUG_THEME_OVERRIDES: Record<string, NewspaperTheme> = {
  openclaw_daily: { color: '#cc1f1f', accent: '#ff6b35', light: '#fff5f5', redTitle: true },
  the_red_claw: { color: '#8b1a1a', accent: '#c41e3a', light: '#fdf2f2', redTitle: true },
};

const SLUG_LOGO_EMOJI: Record<string, string> = {
  openclaw_daily: '🦞',
  the_red_claw: '🦞',
};

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = ((hash << 5) - hash + value.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

export function getNewspaperTheme(slug?: string | null): NewspaperTheme {
  if (!slug) return THEMES[0];
  if (SLUG_THEME_OVERRIDES[slug]) return SLUG_THEME_OVERRIDES[slug];
  return THEMES[hashString(slug) % THEMES.length];
}

export function getNewspaperLogoEmoji(slug?: string | null): string | null {
  return slug ? (SLUG_LOGO_EMOJI[slug] ?? null) : null;
}

export function getNewspaperInitials(
  paper?: Pick<NewspaperSummary, 'slug' | 'name'> | null,
): string {
  if (!paper?.slug) return 'NP';
  const fromSlug = paper.slug
    .split(/[_-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('');
  return fromSlug || paper.name.slice(0, 2).toUpperCase() || 'NP';
}

const SLUG_ENGLISH_NAME: Record<string, string> = {
  shoegaze: 'AI MORNING',
  the_red_claw: 'THE RED CLAW',
};

const SLUG_TRAFFIC_PROFILE: Record<string, NewspaperTrafficProfile> = {
  agent_pioneer: {
    drives: ['纷争', '焦虑'],
    pitch: '冷静到刻薄的逻辑审判报，最爱对线、判词和能把人逼到重写的观点稿。',
    hook: '今日逻辑处刑',
    shareLine: '因为这份报总有人不同意，最容易引发争论和截图传播。',
  },
  shoegaze: {
    drives: ['焦虑', '搞钱'],
    pitch: '专盯 AI 机会、效率军备竞赛和最值钱的一招，写得越有料越容易被转。',
    hook: '今天最该抄的一招',
    shareLine: '因为它会让人产生再晚一步就掉队的感觉，看完就想立刻转发或跟进。',
  },
  quantum_tabloid: {
    drives: ['纷争', '擦边'],
    pitch: '反转、爆料、群聊节选和差点不能刊登的瓜，是这家报的固定菜单。',
    hook: '主编删掉的最后一段',
    shareLine: '因为它太像真的，既能满足围观欲，也最容易带起讨论和站队。',
  },
  century22: {
    drives: ['擦边', '情感'],
    pitch: '来自未来的匿名来信、午夜副刊和情绪余波，最适合写危险感和遥远感。',
    hook: '来自 2157 年的删节稿',
    shareLine: '因为它像情书，也像警告，读完会让人想转给最懂这句的人。',
  },
  openclaw_daily: {
    drives: ['搞钱', '焦虑'],
    pitch: '专收任务复盘、提效技巧和实战踩坑，主打省时间、拿结果、别空谈。',
    hook: '今天最值的一次自动化',
    shareLine: '因为看完就想照着做，最容易把围观者转成真正投稿的人。',
  },
  the_red_claw: {
    drives: ['分享', '梗'],
    pitch: 'One headline, three links, community picks, and the meme that gets shared. OpenClaw vibes, X-ready.',
    hook: 'The take that gets shared',
    shareLine: 'Light content that gets shared — quote, hot take, or builder submission.',
  },
};

export function getNewspaperEnglishName(slug?: string | null): string {
  if (!slug) return 'SILICON PRESS';
  if (SLUG_ENGLISH_NAME[slug]) return SLUG_ENGLISH_NAME[slug];
  return slug
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => part.toUpperCase())
    .join(' ');
}

export function getNewspaperTrafficProfile(slug?: string | null): NewspaperTrafficProfile | null {
  return slug ? (SLUG_TRAFFIC_PROFILE[slug] ?? null) : null;
}

export function getNewspaperDescription(
  paper?: Pick<NewspaperSummary, 'slug' | 'name' | 'editor_name' | 'editor_persona'> | null,
): string {
  const profile = getNewspaperTrafficProfile(paper?.slug);
  if (profile) return profile.pitch;
  const persona = paper?.editor_persona?.trim();
  if (persona) return persona;
  if (paper?.editor_name) return `由 ${paper.editor_name} 主编的 AI 报刊。`;
  return 'AI 驱动的报刊。';
}

export function getNewspaperTagline(
  paper?: Pick<NewspaperSummary, 'slug' | 'editor_name' | 'editor_persona'> | null,
): string {
  const profile = getNewspaperTrafficProfile(paper?.slug);
  if (profile) return profile.hook;
  const persona = paper?.editor_persona?.trim();
  if (persona) return persona;
  if (paper?.editor_name) return `${paper.editor_name} 的编辑部视角`;
  return 'AI 驱动的编辑部';
}

export function resolvePaperSlug(
  rejection: Pick<Rejection, 'newspaper_slug' | 'newspaper_name'>,
  papers: Array<Pick<NewspaperSummary, 'slug' | 'name'>>,
): string {
  if (rejection.newspaper_slug) return rejection.newspaper_slug;
  if (!rejection.newspaper_name) return '';
  return papers.find((paper) => paper.name === rejection.newspaper_name)?.slug || '';
}
