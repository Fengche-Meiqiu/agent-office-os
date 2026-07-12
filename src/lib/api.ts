/**
 * API 统一入口（V2 修复）
 * 仅导出真实后端 API；生产代码不再包含 Mock 分支
 *
 * V2 关键修复：
 * 1. 导出 officeAgentApi（之前错误导出为 officeApi，导致 hooks 找不到）
 * 2. 新增 skillApi 导出
 *
 * 在 hooks 中统一用 import { xxxApi } from '@/lib/api' 引用
 */

export {
  marketplaceApi,
  officeAgentApi,
  chatApi,
  taskApi,
  meetingApi,
  outputApi,
  eventLogApi,
  skillApi,
  createSSEConnection,
} from './realApi';
