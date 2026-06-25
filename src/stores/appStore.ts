import { create } from 'zustand';

interface AppState {
  // 侧边栏折叠状态
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // 当前选中聊天的 Agent ID
  selectedChatAgentId: string | null;
  setSelectedChatAgentId: (id: string | null) => void;

  // 当前选中成果 ID
  selectedOutputId: string | null;
  setSelectedOutputId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  selectedChatAgentId: null,
  setSelectedChatAgentId: (id) => set({ selectedChatAgentId: id }),

  selectedOutputId: null,
  setSelectedOutputId: (id) => set({ selectedOutputId: id }),
}));
