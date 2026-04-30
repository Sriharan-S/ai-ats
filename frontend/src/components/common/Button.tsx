import * as React from "react";
import { forwardRef } from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
  neon?: boolean;
}

const variantStyles: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-blue-500 hover:bg-blue-600 text-white border-transparent hover:border-foreground/50",
  secondary:
    "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-slate-700",
  outline:
    "bg-blue-500/5 hover:bg-blue-500/0 border-blue-500/20 text-blue-600 dark:text-blue-300",
  ghost:
    "border-transparent bg-transparent text-slate-700 dark:text-slate-200 hover:border-zinc-600 hover:bg-black/5 dark:hover:bg-white/10",
  danger:
    "bg-rose-600 hover:bg-rose-700 text-white border-transparent hover:border-foreground/50",
};

const sizeStyles: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "px-4 py-0.5 text-sm",
  md: "px-7 py-1.5",
  lg: "px-10 py-2.5 text-lg",
  icon: "h-10 w-10 flex items-center justify-center p-0",
};

const neonAccentColor: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "via-white/80",
  secondary: "via-blue-500 dark:via-blue-400",
  outline: "via-blue-600 dark:via-blue-400",
  ghost: "via-blue-500 dark:via-blue-400",
  danger: "via-white/80",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading,
      neon = true,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const isIcon = size === "icon";
    const showNeon = neon && !isIcon;
    const accent = neonAccentColor[variant];

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "relative group inline-flex items-center justify-center border text-foreground text-center rounded-full font-medium",
          "transition-all duration-300 ease-out",
          "hover:-translate-y-0.5 hover:shadow-[0_8px_24px_-6px_rgba(59,130,246,0.45)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent",
          "disabled:pointer-events-none disabled:opacity-50",
          "active:translate-y-0 active:scale-[0.98]",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {showNeon && (
          <span
            aria-hidden="true"
            className={cn(
              "pointer-events-none absolute inset-x-0 top-0 h-px mx-auto w-3/4",
              "bg-gradient-to-r from-transparent to-transparent",
              "opacity-0 group-hover:opacity-100 transition-opacity duration-500 ease-in-out",
              accent
            )}
          />
        )}
        {isLoading ? (
          <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : null}
        <span className="relative z-10 inline-flex items-center justify-center gap-2">
          {children}
        </span>
        {showNeon && (
          <span
            aria-hidden="true"
            className={cn(
              "pointer-events-none absolute inset-x-0 -bottom-px h-px mx-auto w-3/4",
              "bg-gradient-to-r from-transparent to-transparent",
              "opacity-0 group-hover:opacity-60 transition-opacity duration-500 ease-in-out",
              accent
            )}
          />
        )}
      </button>
    );
  }
);
Button.displayName = "Button";
