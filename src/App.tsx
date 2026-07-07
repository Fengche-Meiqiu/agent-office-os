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
 * 搴旂敤璺敱鎬诲叆鍙?
 * 鎶婃墍鏈夐〉闈㈤兘鎸傚湪 MainLayout 涓嬶紝淇濊瘉宸︿晶杈规爮鍜岄《閮ㄥ鑸竴鐩存樉绀?
 */
export default function App() {
  return (
    <Router>
      <Routes>
        {/* 涓诲竷灞€锛氬寘鍚晶杈规爮銆侀《閮ㄦ爮 */}
        <Route path="/" element={<MainLayout />}>
          {/* 榛樿鎵撳紑鍔炲叕瀹ら椤?*/}
          <Route index element={<Office />} />

          {/* 鍚勪笟鍔￠〉闈?*/}
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

          {/* 鏈煡璺緞鍥炲埌棣栭〉 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  );
}
