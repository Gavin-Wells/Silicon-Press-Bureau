export interface Submission {
  id: number;
  title: string;
  content?: string;
  pen_name?: string;
  contact_email?: string;
  status: 'pending' | 'reviewing' | 'approved' | 'rejected' | 'queued_overflow';
  newspaper_slug?: string;
  score?: number;
  rejection_reason?: string;
  submitted_at: string;
  reviewed_at?: string;
  newspaper_id?: number;
  newspaper_name?: string;
  section_name?: string;
}

export interface Newspaper {
  id: number;
  name: string;
  slug: string;
  editor_name: string;
}

export interface Rejection {
  id: number;
  letter_content: string;
  submission_title: string;
  created_at: string;
  is_featured?: boolean;
  newspaper_id?: number;
  newspaper_slug?: string;
  newspaper_name?: string;
}

export interface Article {
  id: number;
  title: string;
  content: string;
  position?: number;
  author?: string;
  published_at?: string;
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
