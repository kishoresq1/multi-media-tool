const MAX_TEXT_LENGTH = 1200;

export function escapeHtml(value = '') {
  return String(value)
    .slice(0, MAX_TEXT_LENGTH)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function plainText(value = '', maxLength = MAX_TEXT_LENGTH) {
  return String(value)
    .replace(/[<>]/g, '')
    .replace(/@/g, 'at ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, maxLength);
}

export function maskEmail(email = '') {
  const [local, domain] = String(email).split('@');
  if (!local || !domain) return '';
  const prefix = local.slice(0, Math.min(2, local.length));
  return `${prefix}***@${domain}`;
}
