import { ReactNode } from "react";
import { Card, CardContent } from "./Card";
import { cn } from "./Button";

interface StatCardProps {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  className?: string;
  valueClassName?: string;
}

export function StatCard({ label, value, icon, className, valueClassName }: StatCardProps) {
  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardContent className="p-6 flex flex-col justify-between h-full">
        <div className="flex justify-between items-start mb-2">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">{label}</div>
          {icon && <div className="text-slate-400">{icon}</div>}
        </div>
        <div className={cn("text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-200", valueClassName)}>
          {value}
        </div>
      </CardContent>
    </Card>
  );
}
