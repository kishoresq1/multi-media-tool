export function parseJsonResponse(rawText, fallback) {
  if (!rawText || typeof rawText !== 'string') return fallback;
  const cleaned = rawText.replace(/```json|```/g, '').trim();
  try {
    return JSON.parse(cleaned);
  } catch {
    return fallback;
  }
}
