import '@testing-library/jest-dom/vitest';

process.env.MARKETING_DISABLE_LLM = 'true';
process.env.EMAIL_USER = '';
process.env.EMAIL_PASS = '';

if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
