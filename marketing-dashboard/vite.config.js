import { defineConfig } from 'vite';

export default defineConfig({
  esbuild: {
    jsx: 'automatic'
  },
  server: {
    port: 5174,
    proxy: {
      '/mkt': {
        target: 'http://127.0.0.1:3002',
        rewrite: (path) => path.replace(/^\/mkt/, '/api')
      },
      '/api': 'http://127.0.0.1:3002',
      '/osint': {
        target: 'http://127.0.0.1:8000',
        rewrite: (path) => path.replace(/^\/osint/, '/api')
      }
    }
  }
});
