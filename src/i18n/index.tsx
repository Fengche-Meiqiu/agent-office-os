import { createContext, useCallback, useContext, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react';

export type Locale = 'zh-CN' | 'en-US';
const STORAGE_KEY = 'agent-office-locale';

const en: Record<string, string> = {
  '办公室': 'Office', '会议室': 'Meeting Room', '任务中心': 'Tasks', 'Agent 管理': 'Agent Management',
  '聊天中心': 'Chat', '成果中心': 'Outputs', '工具中心': 'Tools', '数据看板': 'Dashboard', '系统设置': 'Settings',
  'AI 虚拟办公系统': 'AI Virtual Office System', '产品负责人': 'Product Owner', '在线': 'Online',
  '人才市场': 'Agent Marketplace', '浏览来自 Hermes 平台的真实 Agent 人才库': 'Browse live Agents synced from Hermes',
  '刷新人才库': 'Sync Agents', '同步中...': 'Syncing...', '搜索 Agent 名称、职位、技能...': 'Search by Agent name, role, or skill...',
  '平台：': 'Platform:', '状态：': 'Status:', '全部': 'All', '共找到': 'Found', '个 Agent': 'Agents',
  '技能': 'Skills', '工具能力': 'Tools', '查看详情': 'View details', '已雇佣': 'Hired', '雇佣': 'Hire',
  '取消': 'Cancel', '确认雇佣': 'Confirm hire', '虚拟办公室': 'Virtual Office',
  '管理你的 AI Agent 团队，查看工作状态，协作完成任务': 'Manage your AI Agent team, monitor work, and collaborate on tasks',
  '创建会议室': 'Create meeting', '添加 Agent': 'Add Agent', 'Agent 工位': 'Agent Desks', '全部区域': 'All areas',
  '邀请新 Agent 入驻': 'Invite an Agent', '暂无任务': 'No tasks', '基本信息': 'Overview',
  '能力 & 技能': 'Capabilities & skills', 'Soul（人格）': 'Soul', 'Skills（技能）': 'Skills',
  'Tools（工具）': 'Tools', 'Tools（工具能力）': 'Tools', 'Memory（记忆）': 'Memory',
  '暂无描述': 'No description', '来源：': 'Source:', '加入时间：': 'Joined:',
  '任务动态': 'Task activity', '全部任务': 'All tasks', '最近活动': 'Recent activity',
  '暂无对话，点击右侧图标开始聊天': 'No messages yet. Use the icon to start chatting.',
  '聊天列表': 'Conversations', '请选择一个 Agent 开始聊天': 'Select an Agent to start chatting',
  '输入消息...': 'Type a message...', '发送': 'Send', '任务已创建': 'Task created',
  '会议主题': 'Meeting topic', '参会 Agent': 'Participants', '开始会议': 'Start meeting', '结束会议': 'End meeting',
  '会议不存在': 'Meeting not found', '会议结果': 'Meeting results', '会议纪要': 'Summary',
  '决策建议': 'Decisions', '行动项': 'Action items', '发送消息': 'Send message',
  '查看和管理所有 Agent 执行的任务': 'View and manage tasks executed by Agents',
  '任务名称': 'Task', '执行员工': 'Agent', '状态': 'Status', '开始时间': 'Started', '结束时间': 'Finished',
  '耗时': 'Duration', '成果': 'Output', '查看成果': 'View output', '暂无任务记录': 'No tasks yet',
  '成果目录': 'Output files', '选择一个文件进行预览': 'Select a file to preview',
  'PDF 预览需要后端支持，当前为占位': 'PDF preview requires backend support', '不支持的文件类型': 'Unsupported file type',
  '管理并查看所有 Agent 可调用的工具能力': 'Manage tools available to Agents', '核心工具': 'Core tools', '专用工具': 'Specialized tools',
  '实时查看 Agent 办公室的运行指标': 'Monitor Agent Office metrics in real time', '任务状态分布': 'Task status',
  'Agent 任务数排行': 'Tasks by Agent', '未找到该员工': 'Agent not found', '返回办公室': 'Back to office',
  '未找到匹配的记忆': 'No matching memory', 'V1 仅支持只读查看，禁止修改': 'Memory is read-only',
  '时间': 'Time', '我': 'Me', '暂无聊天记录': 'No chat history', 'Performance（绩效）': 'Performance',
  'Employment（雇佣信息）': 'Employment', '直属上级': 'Manager', '平台': 'Platform', '待上线': 'Not available',
  '管理界面主题与通知偏好': 'Manage appearance and notification preferences', '外观主题': 'Appearance',
  '切换浅色 / 深色模式': 'Switch between light and dark mode', '当前主题：': 'Current theme:',
  '深色模式': 'Dark mode', '浅色模式': 'Light mode', '切换到浅色': 'Use light mode', '切换到深色': 'Use dark mode',
  '消息通知': 'Notifications', '是否接收任务、会议等提醒': 'Receive task and meeting alerts',
  '启用通知': 'Enable notifications', '语言': 'Language', '选择界面显示语言': 'Choose the interface language',
  '暂无新通知': 'No new notifications', '关闭': 'Close',
};

export function translateText(value: string, locale: Locale): string {
  if (locale === 'zh-CN' || !value.trim()) return value;
  const leading = value.match(/^\s*/)?.[0] ?? '';
  const trailing = value.match(/\s*$/)?.[0] ?? '';
  let result = value.trim();
  for (const [source, target] of Object.entries(en).sort((a, b) => b[0].length - a[0].length)) {
    result = result.split(source).join(target);
  }
  result = result.replace(/与 (.+) 对话/g, 'Chat with $1').replace(/(\d+)\s*分钟/g, '$1 min').replace(/(\d+)\s*小时/g, '$1 hr');
  return leading + result + trailing;
}

type LanguageValue = { locale: Locale; setLocale: (locale: Locale) => void; t: (value: string) => string };
const LanguageContext = createContext<LanguageValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => localStorage.getItem(STORAGE_KEY) === 'en-US' ? 'en-US' : 'zh-CN');
  const setLocale = useCallback((next: Locale) => {
    localStorage.setItem(STORAGE_KEY, next);
    document.documentElement.lang = next;
    setLocaleState(next);
  }, []);
  const value = useMemo(() => ({ locale, setLocale, t: (text: string) => translateText(text, locale) }), [locale, setLocale]);
  return <LanguageContext.Provider value={value}><LocalizedInterface locale={locale}>{children}</LocalizedInterface></LanguageContext.Provider>;
}

function LocalizedInterface({ locale, children }: { locale: Locale; children: ReactNode }) {
  const rootRef = useRef<HTMLDivElement>(null);
  const originals = useRef(new WeakMap<Node, string>());
  useLayoutEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const localize = (node: Node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const original = originals.current.get(node) ?? node.textContent ?? '';
        originals.current.set(node, original);
        const translated = translateText(original, locale);
        if (node.textContent !== translated) node.textContent = translated;
        return;
      }
      if (!(node instanceof HTMLElement)) return;
      for (const attribute of ['placeholder', 'title', 'aria-label']) {
        const current = node.getAttribute(attribute);
        if (!current) continue;
        const key = 'data-i18n-' + attribute;
        const original = node.getAttribute(key) ?? current;
        node.setAttribute(key, original);
        node.setAttribute(attribute, translateText(original, locale));
      }
      node.childNodes.forEach(localize);
    };
    localize(root);
    document.documentElement.lang = locale;
    const observer = new MutationObserver((mutations) => mutations.forEach((m) => {
      if (m.type === 'characterData') localize(m.target);
      m.addedNodes.forEach(localize);
    }));
    observer.observe(root, { childList: true, characterData: true, subtree: true });
    return () => observer.disconnect();
  }, [locale]);
  return <div ref={rootRef} className="contents">{children}</div>;
}

export function useLanguage() {
  const value = useContext(LanguageContext);
  if (!value) throw new Error('useLanguage must be used within LanguageProvider');
  return value;
}

