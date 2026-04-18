import {
  LayoutDashboard,
  ShieldAlert,
  Package,
  Globe,
  Bell,
  Settings,
  HelpCircle
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "../../lib/utils";

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/" },
  { icon: ShieldAlert, label: "CVEs", path: "/cves" },
  { icon: Package, label: "Packages", path: "/packages" },
  { icon: Globe, label: "Repositories", path: "/repos" },
  { icon: Bell, label: "Notifications", path: "/notifications" },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 border-r bg-card flex flex-col h-screen fixed left-0 top-0">
      <div className="p-6 border-b">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-xl">P</span>
          </div>
          <span className="font-bold text-xl tracking-tight">PROPEX</span>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon size={20} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t space-y-1">
        <button className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground w-full transition-colors">
          <Settings size={20} />
          Settings
        </button>
        <button className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground w-full transition-colors">
          <HelpCircle size={20} />
          Help Center
        </button>

        <div className="mt-6 pt-6 border-t">
          <div className="px-3 py-2 bg-primary/5 rounded-xl border border-primary/10">
            <p className="text-xs font-semibold text-primary uppercase tracking-wider">Plan</p>
            <p className="text-sm font-bold mt-1">Enterprise Dev</p>
            <div className="mt-3 h-1.5 w-full bg-primary/10 rounded-full overflow-hidden">
              <div className="h-full w-2/3 bg-primary" />
            </div>
            <p className="text-[10px] text-muted-foreground mt-2">67% of node capacity used</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
