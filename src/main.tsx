import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { LanguageProvider } from './i18n';
import './index.css'

// 创建 React Query 客户端，用于管理后端请求缓存
// 开发环境下把 staleTime 设为 0，避免热更新后缓存和 loading 状态打架
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: import.meta.env.DEV ? 0 : 1000 * 60 * 5,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
      <LanguageProvider>
      <App />
      </LanguageProvider>
  </QueryClientProvider>,
)
