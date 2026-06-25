/**
 * API 统一入口
 * 根据环境变量 VITE_USE_MOCK 自动切换 Mock API 和真实 API
 *
 * 使用方式：
 * - 开发演示（默认）：不设置或设置 VITE_USE_MOCK=true → 使用 Mock API
 * - 对接后端：设置 VITE_USE_MOCK=false → 使用真实后端 API
 *
 * 在 hooks 中统一用 import { xxxApi } from '@/lib/api' 引用
 */

import {
  marketplaceApi as mockMarketplace,
  officeAgentApi as mockOffice,
  chatApi as mockChat,
  taskApi as mockTask,
  meetingApi as mockMeeting,
  outputApi as mockOutput,
  eventLogApi as mockEventLog,
} from './mockApi';
import * as real from './realApi';

// 是否使用 Mock 数据（默认 true，部署时设为 false）
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

/**
 * 统一 API 对象
 * 根据 USE_MOCK 开关，返回 Mock 或真实 API
 */
export const marketplaceApi = USE_MOCK ? mockMarketplace : real.marketplaceApi;
export const officeApi = USE_MOCK ? mockOffice : real.officeApi;
export const chatApi = USE_MOCK ? mockChat : real.chatApi;
export const taskApi = USE_MOCK ? mockTask : real.taskApi;
export const meetingApi = USE_MOCK ? mockMeeting : real.meetingApi;
export const outputApi = USE_MOCK ? mockOutput : real.outputApi;
export const eventLogApi = USE_MOCK ? mockEventLog : real.eventLogApi;
