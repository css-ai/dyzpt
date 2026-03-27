import { defineConfig } from '@vben/vite-config';

const config: ReturnType<typeof defineConfig> = defineConfig(async () => {
  return {
    application: {},
    vite: {
      server: {
        host: true,
        allowedHosts: true,
        proxy: {
          '/api': {
            changeOrigin: true,
            // 后端接口本身就带 /api 前缀，这里不要 rewrite
            target: 'http://localhost:5322',
            ws: true,
          },
        },
      },
    },
  };
});

export default config;
