import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: any;
  action?: ReactNode;
}

export const EmptyState = ({
  title,
  description,
  icon: Icon = Inbox,
  action
}: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center glass-card rounded-3xl border-dashed border-2 border-white/5 animate-in fade-in zoom-in duration-500">
      <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-6">
        <Icon className="w-8 h-8 text-muted-foreground" />
      </div>
      <h3 className="text-xl font-bold tracking-tight">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mt-2 max-w-sm mx-auto leading-relaxed">
          {description}
        </p>
      )}
      {action && <div className="mt-8">{action}</div>}
    </div>
  );
};
