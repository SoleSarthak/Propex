import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";

interface PageWrapperProps {
  children: ReactNode;
}

export const PageWrapper = ({ children }: PageWrapperProps) => {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans antialiased">
      <TopNav />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-10 overflow-x-hidden">
          <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
