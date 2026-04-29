import * as React from "react";
import { forwardRef } from "react";
import { cn } from "./Button";

export interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  label?: string;
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ className, error, label, ...props }, ref) => {
    return (
      <div className="w-full space-y-2">
        {label && <label className="text-sm font-medium leading-none">{label}</label>}
        <textarea
          ref={ref}
          className={cn(
            "flex min-h-[80px] w-full rounded-md border border-slate-200 dark:border-slate-800 bg-transparent px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-rose-500 focus:ring-rose-500",
            className
          )}
          {...props}
        />
        {error && <p className="text-[0.8rem] font-medium text-rose-500">{error}</p>}
      </div>
    );
  }
);
TextArea.displayName = "TextArea";
