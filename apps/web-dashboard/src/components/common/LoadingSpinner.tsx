import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: number;
  className?: string;
  label?: string;
}

export const LoadingSpinner = ({ size = 24, className = "", label }: LoadingSpinnerProps) => {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <div className="relative">
        <Loader2
          size={size}
          className="text-primary animate-spin"
        />
        <div
          className="absolute inset-0 bg-primary/20 blur-lg rounded-full animate-pulse"
          style={{ width: size, height: size }}
        />
      </div>
      {label && (
        <p className="text-xs font-medium text-muted-foreground animate-pulse uppercase tracking-widest">
          {label}
        </p>
      )}
    </div>
  );
};
