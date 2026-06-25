import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { ScrollArea } from '@/components/ui/scroll-area';

export function MainLayout() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <ScrollArea className="flex-1">
          <main className="min-h-[calc(100vh-4rem)] p-6">
            <Outlet />
          </main>
        </ScrollArea>
      </div>
    </div>
  );
}
