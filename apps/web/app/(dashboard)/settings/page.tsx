import { Store, Bot } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
          System Settings
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Configure store details and system preferences.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Store Card */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-2xs space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-foreground">
              <Store className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-xs font-semibold text-foreground">Store Details</h2>
              <p className="text-[10px] text-muted-foreground">Retail business profile</p>
            </div>
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="p-2.5 rounded-lg bg-muted/20 border border-border/60">
              <span className="font-medium text-muted-foreground">Store:</span>{" "}
              <span className="font-semibold text-foreground">Conversational Business OS (CBO)</span>
            </div>
            <div className="p-2.5 rounded-lg bg-muted/20 border border-border/60">
              <span className="font-medium text-muted-foreground">Currency:</span>{" "}
              <span className="font-semibold text-foreground">PKR (Rs)</span>
            </div>
          </div>
        </div>

        {/* Integration Card */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-2xs space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-foreground">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-xs font-semibold text-foreground">AI & WhatsApp</h2>
              <p className="text-[10px] text-muted-foreground">Conversational status</p>
            </div>
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="p-2.5 rounded-lg bg-muted/20 border border-border/60 flex items-center justify-between">
              <span className="font-medium text-muted-foreground">WhatsApp API:</span>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 border border-emerald-200/50">
                Phase 4 Ready
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-muted/20 border border-border/60 flex items-center justify-between">
              <span className="font-medium text-muted-foreground">OpenAI Whisper:</span>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 border border-emerald-200/50">
                Phase 3/5 Ready
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
