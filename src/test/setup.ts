/**
 * vitest 测试 setup 文件
 * 小白解释：这个文件在所有测试开始前执行，用来初始化测试环境
 */
import '@testing-library/jest-dom';

// Mock matchMedia（组件库内部会用到）
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock IntersectionObserver（ScrollArea 等组件会用到）
Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: class IntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  },
});
