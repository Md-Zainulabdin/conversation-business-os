"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Send } from "lucide-react";

import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";

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
import { ProductSelect } from "@/components/assistant/product-select";
import { INTENT_LABEL } from "@/lib/format";

const SUGGESTIONS = [
  "Sold 20 packs of rice",
  "Bought 10 cartons of Coke",
  "Paid 5,000 for electricity",
  "How much Coke stock is left?",
];

const CANCEL_WORDS = new Set([
  "cancel",
  "cancel it",
  "never mind",
  "nevermind",
  "stop",
]);

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
  const [conversationId] = useState<string>(() => nextId());
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

    const hasPending = messages.some(
      (m) =>
        m.role === "assistant" &&
        m.requiresConfirmation &&
        m.command &&
        !m.executed &&
        !m.executing
    );
    const normalizedCancel = trimmed.toLowerCase().replace(/[.!?]+$/, "").trim();
    if (hasPending && CANCEL_WORDS.has(normalizedCancel)) {
      setMessages((prev) => [
        ...prev.map((m) =>
          m.requiresConfirmation && m.command && !m.executed
            ? {
                ...m,
                requiresConfirmation: false,
                busy: false,
                executing: false,
                cancelled: true,
              }
            : m
        ),
        {
          id: nextId(),
          role: "assistant",
          text: "Cancelled. Nothing was recorded.",
        },
      ]);
      setInput("");
      return;
    }

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
        conversation_id: conversationId,
      });

      const assistantMessage: ChatMessage = {
        id: thinkingMessage.id,
        role: "assistant",
        text: proposal.message,
        command: proposal.command,
        requiresConfirmation: proposal.requires_confirmation,
        disambiguation: proposal.disambiguation ?? null,
        issues: proposal.issues ?? null,
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
        idempotency_key: id,
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

  async function resolveCommand(
    id: string,
    command: AICommand,
    productId: string
  ) {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, busy: true } : m))
    );

    try {
      const proposal = await api.post<AIProposalResponse>(
        "/ai/commands/resolve",
        { command, product_id: productId }
      );
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id
            ? {
                ...m,
                text: proposal.message,
                command: proposal.command,
                requiresConfirmation: proposal.requires_confirmation,
                disambiguation: proposal.disambiguation ?? null,
                issues: proposal.issues ?? null,
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
                disambiguation: null,
                error: true,
                errorDetail,
                busy: false,
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
          ? {
              ...m,
              requiresConfirmation: false,
              busy: false,
              executing: false,
              cancelled: true,
            }
          : m
      )
    );
  }

  function renderMessage(m: ChatMessage) {
    if (m.role === "user") {
      return (
        <div className="max-w-full rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">
          <p className="whitespace-pre-line">{m.text}</p>
        </div>
      );
    }

    if (m.disambiguation && m.disambiguation.length > 0 && m.command) {
      return (
        <ProductSelect
          message={m.text}
          candidates={m.disambiguation}
          busy={m.busy}
          onSelect={(productId) =>
            resolveCommand(m.id, m.command!, productId)
          }
        />
      );
    }

    if (m.busy) {
      return (
        <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm text-muted-foreground">
          <Spinner className="size-3.5" />
          <span>Thinking...</span>
        </div>
      );
    }

    if (m.executing && m.command) {
      return (
        <CommandCard
          command={m.command}
          issues={m.issues}
          busy
          onExecute={() => executeCommand(m.id, m.command!)}
          onCancel={() => cancelCommand(m.id)}
        />
      );
    }

    if (m.executed && m.command) {
      return (
        <RecordSuccess
          label={INTENT_LABEL[m.command.intent]}
          command={m.command}
        />
      );
    }

    if (m.cancelled && m.command) {
      return (
        <CommandCard
          command={m.command}
          issues={m.issues}
          cancelled
          onExecute={() => executeCommand(m.id, m.command!)}
          onCancel={() => cancelCommand(m.id)}
        />
      );
    }

    if (m.error) {
      return (
        <ErrorNotice
          title={m.errorDetail?.title || m.text}
          hint={m.errorDetail?.hint}
          options={m.errorDetail?.options}
        />
      );
    }

    if (m.requiresConfirmation && m.command) {
      return (
        <CommandCard
          command={m.command}
          issues={m.issues}
          onExecute={() => executeCommand(m.id, m.command!)}
          onCancel={() => cancelCommand(m.id)}
        />
      );
    }

    if (m.command && m.issues && m.issues.length > 0) {
      return (
        <CommandCard
          command={m.command}
          issues={m.issues}
          blocked
          onExecute={() => executeCommand(m.id, m.command!)}
          onCancel={() => cancelCommand(m.id)}
        />
      );
    }

    return (
      <div className="max-w-[80%] rounded-lg border border-border bg-white px-3 py-2 text-sm text-foreground">
        <p className="whitespace-pre-line">{m.text}</p>
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
          Record sales, purchases and expenses, or just ask about your stock.
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
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : "w-full"}>
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