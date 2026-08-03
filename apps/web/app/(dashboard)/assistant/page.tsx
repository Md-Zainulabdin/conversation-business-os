"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Send } from "lucide-react";

import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

import type {
  AICommand,
  AIExecuteResponse,
  AIProposalResponse,
  ChatMessage,
  ErrorDetail,
} from "@/types";
import { CommandCard } from "@/components/assistant/command-card";
import { RecordSuccess } from "@/components/assistant/record-success";
import { ErrorNotice } from "@/components/assistant/error-notice";
import { INTENT_LABEL } from "@/lib/format";

const SUGGESTIONS = [
  "Sold 20 packs of rice",
  "Bought 10 cartons of Coke",
  "Paid 5,000 for electricity",
  "How much Coke stock is left?",
];

function parseErrorDetail(err: unknown): ErrorDetail {
  if (err instanceof ApiError && err.detail && typeof err.detail === "object") {
    const d = err.detail as { title?: string; hint?: string; options?: string[] };
    return {
      title: d.title || err.message,
      ...(d.hint ? { hint: d.hint } : {}),
      ...(Array.isArray(d.options) && d.options.length
        ? { options: d.options }
        : {}),
    };
  }
  return {
    title:
      err instanceof Error
        ? err.message
        : "Something went wrong. Please try again.",
  };
}

let lastUniqueKey = 0;
function nextId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  lastUniqueKey += 1;
  return `key-${Date.now()}-${lastUniqueKey}`;
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;

    const userMessage: ChatMessage = {
      id: nextId(),
      role: "user",
      text: trimmed,
    };
    const thinkingMessage: ChatMessage = {
      id: nextId(),
      role: "assistant",
      text: "",
      busy: true,
    };

    setMessages((prev) => [...prev, userMessage, thinkingMessage]);
    setInput("");
    setBusy(true);

    try {
      const proposal = await api.post<AIProposalResponse>("/ai/commands", {
        message: trimmed,
      });

      const assistantMessage: ChatMessage = {
        id: thinkingMessage.id,
        role: "assistant",
        text: proposal.message,
        command: proposal.command,
        requiresConfirmation: proposal.requires_confirmation,
      };

      setMessages((prev) =>
        prev.map((m) => (m.id === thinkingMessage.id ? assistantMessage : m))
      );
    } catch (err) {
      const errorDetail = parseErrorDetail(err);
      const errorMessage: ChatMessage = {
        id: thinkingMessage.id,
        role: "assistant",
        text: errorDetail.title,
        error: true,
        errorDetail,
      };
      setMessages((prev) =>
        prev.map((m) => (m.id === thinkingMessage.id ? errorMessage : m))
      );
    } finally {
      setBusy(false);
    }
  }

  async function executeCommand(id: string, command: AICommand) {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, executing: true, busy: false } : m
      )
    );

    try {
      const result = await api.post<AIExecuteResponse>("/ai/commands/execute", {
        command,
      });
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id
            ? {
                ...m,
                text: result.message,
                requiresConfirmation: false,
                executing: false,
                executed: true,
                busy: false,
              }
            : m
        )
      );
    } catch (err) {
      const errorDetail = parseErrorDetail(err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id
            ? {
                ...m,
                text: errorDetail.title,
                requiresConfirmation: false,
                executing: false,
                busy: false,
                error: true,
                errorDetail,
              }
            : m
        )
      );
    }
  }

  function cancelCommand(id: string) {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id
          ? { ...m, requiresConfirmation: false, busy: false, executing: false }
          : m
      )
    );
  }

  function renderMessage(m: ChatMessage) {
    if (m.role === "user") {
      return (
        <div className="flex justify-end">
          <div className="max-w-full rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">
            <p className="whitespace-pre-line">{m.text}</p>
          </div>
        </div>
      );
    }

    if (m.busy) {
      return (
        <div className="flex">
          <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm text-muted-foreground">
            <Spinner className="size-3.5" />
            <span>Thinking...</span>
          </div>
        </div>
      );
    }

    if (m.executing && m.command) {
      return (
        <div className="flex">
          <div className="w-full max-w-2xl">
            <CommandCard
              command={m.command}
              busy
              onExecute={() => executeCommand(m.id, m.command!)}
              onCancel={() => cancelCommand(m.id)}
            />
          </div>
        </div>
      );
    }

    if (m.executed && m.command) {
      return (
        <div className="flex">
          <div className="w-full max-w-2xl">
            <RecordSuccess
              label={INTENT_LABEL[m.command.intent]}
              message={m.text}
            />
          </div>
        </div>
      );
    }

    if (m.error) {
      return (
        <div className="flex">
          <div className="w-full max-w-2xl">
            <ErrorNotice
              title={m.errorDetail?.title || m.text}
              hint={m.errorDetail?.hint}
              options={m.errorDetail?.options}
            />
          </div>
        </div>
      );
    }

    if (m.requiresConfirmation && m.command) {
      return (
        <div className="flex">
          <div className="w-full max-w-2xl">
            <CommandCard
              command={m.command}
              onExecute={() => executeCommand(m.id, m.command!)}
              onCancel={() => cancelCommand(m.id)}
            />
          </div>
        </div>
      );
    }

    return (
      <div className="flex">
        <div className="max-w-[80%] rounded-lg border border-border bg-white px-3 py-2 text-sm text-foreground">
          <p className="whitespace-pre-line">{m.text}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-7.5rem)] flex-col">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-foreground">
          AI Assistant
        </h1>
        <p className="mt-0.5 text-[13px] text-muted-foreground">
          Record sales, purchases and expenses — or just ask about your stock.
        </p>
      </div>

      <div
        ref={scrollRef}
        className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4 [scrollbar-width:thin] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-border"
      >
        {messages.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <Bot className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                How can I help with your business today?
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Try one of these:
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => sendMessage(s)}
                  className="rounded-full border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            {renderMessage(m)}
          </div>
        ))}
      </div>

      <form
        className="mx-auto mb-6 flex w-full max-w-3xl items-center gap-2 rounded-2xl border border-border bg-background px-3 py-2 shadow-sm transition-colors focus-within:border-primary/50"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder='Try "Sold 20 packs of rice" or ask about your stock...'
          autoFocus
          className="border-0 bg-transparent shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
        />
        <Button
          type="submit"
          disabled={busy || !input.trim()}
          size="icon"
          className="shrink-0 rounded-full"
        >
          <Send className="size-4" />
        </Button>
      </form>
    </div>
  );
}