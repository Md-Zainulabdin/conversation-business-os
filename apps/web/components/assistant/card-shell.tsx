"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type CardVariant = "default" | "success" | "error";

const VARIANT_STYLES: Record<
  CardVariant,
  { border: string; bg: string; headerBg: string; headerBorder: string }
> = {
  default: {
    border: "border-border",
    bg: "bg-white",
    headerBg: "bg-muted/40",
    headerBorder: "border-border",
  },
  success: {
    border: "border-emerald-200",
    bg: "bg-emerald-50",
    headerBg: "bg-emerald-100/60",
    headerBorder: "border-emerald-200",
  },
  error: {
    border: "border-red-200",
    bg: "bg-red-50",
    headerBg: "bg-red-100/60",
    headerBorder: "border-red-200",
  },
};

interface CardShellProps {
  variant?: CardVariant;
  className?: string;
  children: ReactNode;
}

export function CardShell({
  variant = "default",
  className,
  children,
}: CardShellProps) {
  const s = VARIANT_STYLES[variant];

  return (
    <div
      className={cn(
        "w-full max-w-lg overflow-hidden rounded-lg border",
        s.border,
        s.bg,
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  icon: ReactNode;
  label: string;
  variant?: CardVariant;
  trailing?: ReactNode;
  className?: string;
}

export function CardHeader({
  icon,
  label,
  variant = "default",
  trailing,
  className,
}: CardHeaderProps) {
  const s = VARIANT_STYLES[variant];

  const labelColor: Record<CardVariant, string> = {
    default: "text-primary",
    success: "text-emerald-700",
    error: "text-red-700",
  };

  return (
    <div
      className={cn(
        "flex items-center justify-between border-b px-4 py-2.5",
        s.headerBg,
        s.headerBorder,
        className
      )}
    >
      <span
        className={cn(
          "inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide",
          labelColor[variant]
        )}
      >
        {icon}
        {label}
      </span>
      {trailing}
    </div>
  );
}

interface CardBodyProps {
  children: ReactNode;
  variant?: CardVariant;
  className?: string;
  noPadding?: boolean;
}

export function CardBody({
  children,
  variant = "default",
  className,
  noPadding,
}: CardBodyProps) {
  const s = VARIANT_STYLES[variant];

  return (
    <div
      className={cn(
        "border-b",
        s.headerBorder,
        !noPadding && "px-4 py-3",
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardFooterProps {
  children: ReactNode;
  variant?: CardVariant;
  className?: string;
}

export function CardFooter({
  children,
  variant = "default",
  className,
}: CardFooterProps) {
  const s = VARIANT_STYLES[variant];

  return (
    <div
      className={cn(
        "flex items-center gap-2 border-t px-4 py-3",
        s.headerBorder,
        className
      )}
    >
      {children}
    </div>
  );
}
