import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// 从环境变量读取配置，提供合理的默认值
const FRONTEND_HOST = process.env.VITE_FRONTEND_HOST || '0.0.0.0';
const FRONTEND_PORT = parseInt(process.env.VITE_FRONTEND_PORT || '19001', 10);
const API_HOST = process.env.VITE_API_HOST || '127.0.0.1';
const API_PORT = parseInt(process.env.VITE_API_PORT || '19002', 10);
const HMR_HOST = process.env.VITE_HMR_HOST || 'localhost';
const HMR_PORT = parseInt(process.env.VITE_HMR_PORT || FRONTEND_PORT, 10);

export default defineConfig({
  plugins: [vue()],
  server: {
    port: FRONTEND_PORT,
    host: FRONTEND_HOST,
    middlewareMode: false,
    hmr: {
      protocol: 'ws',
      host: HMR_HOST,
      port: HMR_PORT,
    },
    proxy: {
      // API 代理：处理所有 /api 请求
      '/api': {
        target: `http://${API_HOST}:${API_PORT}`,
        changeOrigin: true,
        secure: false,
        ws: false,
        logLevel: 'debug',
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            console.error('❌ API Proxy error:', err.message);
            res.writeHead(503, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Backend service unavailable', details: err.message }));
          });
          proxy.on('proxyRes', (proxyRes, req) => {
            console.log(`✅ [API Proxy] ${req.method} ${req.url} -> ${proxyRes.statusCode}`);
          });
        },
      },
      // WebSocket 代理：处理所有 /ws 请求
      // 注意：必须在 /api 之后定义，因为 /ws 路径更具体
      '/ws': {
        target: `ws://${API_HOST}:${API_PORT}`,
        changeOrigin: true,
        ws: true,
        rejectUnauthorized: false,
        logLevel: 'debug',
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.error('❌ WebSocket Proxy error:', err.message);
          });
          proxy.on('proxyRes', (proxyRes, req) => {
            console.log(`✅ [WS Proxy] WebSocket connection established for ${req.url}`);
          });
          proxy.on('upgrade', (req) => {
            console.log(`🔌 [WS Proxy] Upgrading connection for ${req.url}`);
          });
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
