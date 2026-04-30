import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';
import path from 'path';
import { defineConfig } from 'vite';

function readBackendPort(): string {
  const envPath = path.resolve(__dirname, '..', 'backend', '.env');
  const content = fs.readFileSync(envPath, 'utf-8');
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const idx = trimmed.indexOf('=');
    if (idx === -1) continue;
    if (trimmed.slice(0, idx).trim() === 'PORT') {
      return trimmed.slice(idx + 1).trim().replace(/^['"]|['"]$/g, '');
    }
  }
  throw new Error(`PORT not defined in ${envPath}`);
}

const backendPort = readBackendPort();

export default defineConfig(() => ({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
  server: {
    hmr: process.env.DISABLE_HMR !== 'true',
    allowedHosts: ['ats.sriharan.me'],
    proxy: {
      '/api': `http://localhost:${backendPort}`,
    },
  },
}));