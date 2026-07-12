/**
 * ErrorBoundary 错误边界组件（V2 新增）
 *
 * 小白解释：当页面里某个组件报错崩了，不会让整个页面白屏，
 * 而是显示一个友好的错误提示，让你可以继续操作其他部分。
 *
 * 用法：在 App.tsx 里把容易出错的组件包一层
 *   <ErrorBoundary>
 *     <MeetingRoom />
 *   </ErrorBoundary>
 */
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  // 捕获子组件抛出的错误
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  // 记录错误信息（方便调试）
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[ErrorBoundary] 捕获到错误:', error, errorInfo);
  }

  // 重置错误状态，让用户可以重试
  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // 如果有自定义 fallback，用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误提示
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-950">
            <h3 className="mb-2 text-lg font-semibold text-red-700 dark:text-red-300">
              出错了
            </h3>
            <p className="mb-4 text-sm text-red-600 dark:text-red-400">
              {this.state.error?.message || '组件渲染时发生未知错误'}
            </p>
            <button
              onClick={this.handleReset}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              重试
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
