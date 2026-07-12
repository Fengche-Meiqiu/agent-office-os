import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";
import Office from "@/pages/Office";
import Marketplace from "@/pages/Marketplace";
import Chat from "@/pages/Chat";
import Tasks from "@/pages/Tasks";
import Outputs from "@/pages/Outputs";
import Meeting from "@/pages/Meeting";
import Profile from "@/pages/Profile";
import Tools from "@/pages/Tools";
import Settings from "@/pages/Settings";
import Dashboard from "@/pages/Dashboard";

/**
 * 应用路由总入口
 * 把所有页面都挂在 MainLayout 下，保证左侧边栏和顶部导航一直显示
 */
export default function App() {
  return (
    <Router>
      <Routes>
        {/* 主布局：包含侧边栏、顶部栏 */}
        <Route path="/" element={<MainLayout />}>
          {/* 默认打开办公室首页 */}
          <Route index element={<Office />} />

          {/* 各业务页面 */}
          <Route path="marketplace" element={<Marketplace />} />
          <Route path="chat" element={<Chat />} />
          <Route path="chat/:id" element={<Chat />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="outputs" element={<Outputs />} />
          <Route path="meeting" element={<Meeting />} />
          <Route path="meeting/:id" element={<Meeting />} />
          <Route path="profile/:id" element={<Profile />} />
          <Route path="tools" element={<Tools />} />
          <Route path="settings" element={<Settings />} />
          <Route path="dashboard" element={<Dashboard />} />

          {/* 未知路径回到首页 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  );
}
