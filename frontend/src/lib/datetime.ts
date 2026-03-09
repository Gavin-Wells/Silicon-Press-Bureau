const TZ_SUFFIX_RE = /([zZ]|[+\-]\d{2}:\d{2})$/;

function parseApiDate(input: string): Date {
  const value = input.trim();
  // 后端常返回无时区时间戳；按 UTC 解释后再统一转上海时区展示。
  const normalized = TZ_SUFFIX_RE.test(value) ? value : `${value}Z`;
  return new Date(normalized);
}

export function formatShanghaiDate(input: string): string {
  const date = parseApiDate(input);
  if (Number.isNaN(date.getTime())) return input;
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

export function formatShanghaiDateTime(input: string): string {
  const date = parseApiDate(input);
  if (Number.isNaN(date.getTime())) return input;
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}
