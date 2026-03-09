import type { Rejection } from '../types';

import { getAccessToken } from '../lib/auth';

const configuredApiBase = ((import.meta as any).env?.VITE_API_URL as string | undefined)?.replace(/\/$/, '');
const API_V1 = configuredApiBase ? `${configuredApiBase}/api/v1` : '/api/v1';
const PRIORITY_NEWSPAPER_SLUGS: Record<string, number> = {
  shoegaze: 0,
  openclaw_daily: 1,
  the_red_claw: 2,
};

function authHeaders(includeJson = false): Record<string, string> {
  const token = getAccessToken();
  const h: Record<string, string> = {};
  if (token) h['Authorization'] = `Bearer ${token}`;
  if (includeJson) h['Content-Type'] = 'application/json';
  return h;
}

export interface SectionInfo {
  slug: string;
  name: string;
  description: string;
  min_chars: number;
  max_chars: number;
  scoring_dimensions: { name: string; weight: number; description: string }[];
}

export interface NewspaperSummary {
  id: number;
  name: string;
  slug: string;
  editor_name: string;
  editor_persona?: string | null;
  pass_threshold: number;
}

function sortNewspapers<T extends { id: number; slug: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const aPriority = PRIORITY_NEWSPAPER_SLUGS[a.slug] ?? 999;
    const bPriority = PRIORITY_NEWSPAPER_SLUGS[b.slug] ?? 999;
    if (aPriority !== bPriority) return aPriority - bPriority;
    return a.id - b.id;
  });
}

export interface LiveIssueMeta {
  newspaper_name: string;
  newspaper_slug: string;
  issue_date: string;
  issue_number?: number;
  template_used?: string;
  article_count: number;
  editor_message?: string;
  published_at?: string;
}

export interface LiveLayoutItemDivider {
  type: 'divider';
}

export interface LiveLayoutItemQuote {
  type: 'quote';
  text: string;
  author?: string;
}

export interface LiveLayoutItemBox {
  type: 'box';
  title: string;
  content: string;
}

export interface LiveLayoutItemAd {
  type: 'ad';
  style?: 'classified' | 'display';
}

export interface LiveLayoutItemArticle {
  type: 'article';
  id: number | string;
  title: string;
  content: string;
  author: string;
  column: string;
  importance: 'headline' | 'secondary' | 'brief';
}

export type LiveLayoutItem =
  | LiveLayoutItemDivider
  | LiveLayoutItemQuote
  | LiveLayoutItemBox
  | LiveLayoutItemAd
  | LiveLayoutItemArticle;

export interface LiveLayoutColumn {
  width: number;
  items: LiveLayoutItem[];
}

export interface LiveLayoutPage {
  page_num: number;
  section_name: string;
  template_used: string;
  columns: LiveLayoutColumn[];
}

export interface LiveIssueResponse {
  status: 'published' | 'pending_publish';
  newspaper_slug: string;
  issue_meta: LiveIssueMeta | null;
  pages: LiveLayoutPage[];
}

export interface LeaderboardEntry {
  submission_id: number;
  title: string;
  pen_name: string;
  score: number;
  section_slug: string;
  section_name: string;
  newspaper_slug: string;
  newspaper_name: string;
  reviewed_at: string;
  submitted_at: string;
}

export interface NearMissEntry extends LeaderboardEntry {
  distance_to_headline: number;
  story_label: string;
}

export interface SpicyRejectionEntry {
  id: number;
  submission_id: number;
  submission_title: string;
  pen_name: string;
  newspaper_slug: string;
  newspaper_name: string;
  letter_content: string;
  created_at: string;
  spice_score: number;
}

export interface DailyLeaderboardResponse {
  time_window_hours: number;
  window_start: string;
  window_end: string;
  entry_count: number;
  top_headline: LeaderboardEntry | null;
  section_leaders: LeaderboardEntry[];
  near_misses: NearMissEntry[];
  recent_challengers: LeaderboardEntry[];
  spicy_rejections: SpicyRejectionEntry[];
}

export interface UserInfo {
  id: number;
  username: string;
  email?: string | null;
  pen_name?: string | null;
  created_at: string;
}

export interface OverviewStatsResponse {
  today_submissions: number;
  approval_rate: number;
  today_rejections: number;
  pending_total: number;
  total_visitors: number;
  today_visitors: number;
}

export interface RejectionPageResponse {
  items: Rejection[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export const api = {
  // ── 板块 ──
  async getSections(newspaperSlug: string): Promise<SectionInfo[]> {
    const res = await fetch(`${API_V1}/sections/${newspaperSlug}`);
    return res.json();
  },

  // ── 投稿 ──
  async submitArticle(data: {
    newspaper_slug: string;
    section_slug: string;
    title: string;
    content: string;
    pen_name?: string;
    contact_email?: string;
  }) {
    const res = await fetch(`${API_V1}/submissions`, {
      method: 'POST',
      headers: authHeaders(true),
      credentials: 'include',
      body: JSON.stringify({
        ...data,
        pen_name: data.pen_name || '匿名',
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '投稿失败');
    }
    return res.json();
  },

  async getSubmission(id: number) {
    const res = await fetch(`${API_V1}/submissions/${id}`);
    return res.json();
  },

  async getSubmissionsByPenName(penName: string) {
    const res = await fetch(`${API_V1}/submissions/by-pen-name/${encodeURIComponent(penName)}`);
    return res.json();
  },

  async getMySubmissions() {
    const res = await fetch(`${API_V1}/submissions/me`, { headers: authHeaders() });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '获取投稿失败');
    }
    return res.json();
  },

  // 用户投稿列表 (通过笔名查询)
  async getUserSubmissions(penName: string = '匿名') {
    const res = await fetch(`${API_V1}/submissions/by-pen-name/${encodeURIComponent(penName)}`);
    return res.json();
  },

  // ── 用户 ──
  async login(data: { username: string; password: string; pen_name?: string; email?: string }): Promise<{ user: UserInfo; access_token: string }> {
    const res = await fetch(`${API_V1}/users/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '登录失败');
    }
    return res.json();
  },

  // ── 报纸 ──
  async getNewspapers(): Promise<NewspaperSummary[]> {
    const res = await fetch(`${API_V1}/newspapers`);
    if (!res.ok) {
      throw new Error('获取报刊列表失败');
    }
    const items = await res.json();
    return sortNewspapers(items);
  },

  async getLatestIssue(slug: string) {
    const res = await fetch(`${API_V1}/newspapers/${slug}/latest`);
    return res.json();
  },

  async getLatestLiveIssue(slug: string): Promise<LiveIssueResponse> {
    const res = await fetch(`${API_V1}/newspapers/${slug}/latest-live`);
    if (!res.ok) {
      throw new Error('获取最新版面失败');
    }
    return res.json();
  },

  /** 一次拉取所有报纸最新版面，供首页使用，避免 N 次请求 */
  async getLatestLiveIssueAll(compact: boolean = false): Promise<Record<string, LiveIssueResponse>> {
    const params = new URLSearchParams();
    if (compact) params.set('compact', 'true');
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_V1}/newspapers/latest-live-all${suffix}`);
    if (!res.ok) {
      throw new Error('获取最新版面失败');
    }
    return res.json();
  },

  async getLatestLiveIssueForAdmin(
    slug: string,
    adminUser: string,
  ): Promise<LiveIssueResponse> {
    const params = new URLSearchParams();
    params.set('admin_user', adminUser);
    params.set('include_tomorrow_preview', 'true');
    const res = await fetch(`${API_V1}/newspapers/${slug}/latest-live?${params.toString()}`);
    if (!res.ok) {
      throw new Error('获取预览版面失败');
    }
    return res.json();
  },

  async getIssueByDate(slug: string, issueDate: string): Promise<LiveIssueResponse> {
    const res = await fetch(`${API_V1}/newspapers/${slug}/issues/${issueDate}`);
    if (!res.ok) {
      throw new Error('获取指定期号失败');
    }
    return res.json();
  },

  // ── 退稿 ──
  async getFeaturedRejections(page: number = 1, pageSize: number = 12): Promise<RejectionPageResponse> {
    const params = new URLSearchParams();
    params.set('page', String(page));
    params.set('page_size', String(pageSize));
    const res = await fetch(`${API_V1}/rejections/featured?${params.toString()}`);
    return res.json();
  },

  // ── 首页统计 ──
  async getOverviewStats(): Promise<OverviewStatsResponse> {
    const res = await fetch(`${API_V1}/stats/overview`);
    if (!res.ok) {
      throw new Error('获取首页统计失败');
    }
    return res.json();
  },

  // ── 榜单 ──
  async getDailyLeaderboard(newspaperSlug?: string, windowHours: number = 24): Promise<DailyLeaderboardResponse> {
    const params = new URLSearchParams();
    params.set('window_hours', String(windowHours));
    if (newspaperSlug) {
      params.set('newspaper_slug', newspaperSlug);
    }
    const res = await fetch(`${API_V1}/leaderboard/daily?${params.toString()}`);
    if (!res.ok) {
      throw new Error('获取榜单失败');
    }
    return res.json();
  },
};
