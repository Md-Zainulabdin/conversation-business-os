import { cn } from "@/lib/utils";

const PRESETS = [
  "#266df0", "#0ea5e9", "#06b6d4", "#10b981", "#84cc16",
  "#eab308", "#f97316", "#ef4444", "#ec4899", "#a855f7",
];

interface ColorPickerProps {
  value: string | null;
  onChange: (color: string | null) => void;
}

export function ColorPicker({ value, onChange }: ColorPickerProps) {
  return (
    <div className="flex flex-wrap gap-1.5">
      <button
        type="button"
        onClick={() => onChange(null)}
        className={cn(
          "h-7 w-7 rounded-lg border border-border transition-colors hover:border-muted-foreground cursor-pointer",
          !value && "ring-2 ring-ring ring-offset-1",
        )}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="#9fa1a7" strokeWidth="2" className="h-full w-full p-1">
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
      </button>
      {PRESETS.map((color) => (
        <button
          key={color}
          type="button"
          style={{ backgroundColor: color }}
          onClick={() => onChange(color)}
          className={cn(
            "h-7 w-7 rounded-lg border border-border transition-transform hover:scale-110 cursor-pointer",
            value === color && "ring-2 ring-ring ring-offset-1",
          )}
        />
      ))}
    </div>
  );
}
