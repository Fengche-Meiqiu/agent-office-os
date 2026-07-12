/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

// vitest 配置文件
// 小白解释：这是前端测试的配置，告诉 vitest 用 React 插件、路径别名怎么解析
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    // 测试环境：jsdom（模拟浏览器 DOM）
    environment: 'jsdom',
    // 测试文件位置
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    // 全局变量（describe/it/expect 等）
    globals: true,
    // setup 文件（在所有测试前执行）
    setupFiles: ['./src/test/setup.ts'],
    // 覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
})
