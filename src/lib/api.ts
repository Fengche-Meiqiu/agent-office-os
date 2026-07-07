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

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export const marketplaceApi = USE_MOCK ? mockMarketplace : real.marketplaceApi;
export const officeAgentApi = USE_MOCK ? mockOffice : real.officeAgentApi;
export const officeApi = officeAgentApi;
export const chatApi = USE_MOCK ? mockChat : real.chatApi;
export const taskApi = USE_MOCK ? mockTask : real.taskApi;
export const meetingApi = USE_MOCK ? mockMeeting : real.meetingApi;
export const outputApi = USE_MOCK ? mockOutput : real.outputApi;
export const eventLogApi = USE_MOCK ? mockEventLog : real.eventLogApi;
