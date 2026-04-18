import { Search, Bell, Menu } from "lucide-react";

export const TopNav = () => {
  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between w-full h-16 px-6 border-b bg-background/95 backdrop-blur">
      <div className="flex items-center gap-4">
        <button className="p-2 -ml-2 rounded-md hover:bg-muted lg:hidden">
          <Menu className="w-5 h-5" />
        </button>
        <div className="hidden lg:flex items-center gap-2 font-bold text-xl tracking-tight text-primary">
          <span className="w-8 h-8 bg-primary text-primary-foreground rounded-lg flex items-center justify-center">P</span>
          Propex
        </div>
      </div>

      <div className="flex-1 max-w-md mx-8 hidden md:block">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search CVEs, packages..."
            className="w-full h-9 pl-10 pr-4 rounded-full border bg-muted/50 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="p-2 rounded-full hover:bg-muted relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full" />
        </button>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent cursor-pointer" />
      </div>
    </nav>
  );
};
