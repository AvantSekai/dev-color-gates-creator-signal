"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { askQuestion, type ChatResponse, type ChatSource } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  kind?: ChatResponse["kind"];
  sources?: ChatSource[];
}

const KIND_LABEL: Record<ChatResponse["kind"], string> = {
  computed: "Computed from data",
  grounded_opinion: "Opinion, grounded in data",
  opinion: "AI opinion",
};

const KIND_STYLE: Record<ChatResponse["kind"], string> = {
  computed: "bg-emerald-100 text-emerald-800",
  grounded_opinion: "bg-sky-100 text-sky-800",
  opinion: "bg-amber-100 text-amber-800",
};

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await askQuestion(question);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: response.answer,
          kind: response.kind,
          sources: response.sources,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex h-screen max-w-2xl flex-col px-6 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Ask about the creators</h1>
        <Link href="/" className="text-sm underline">
          &larr; Summary
        </Link>
      </div>

      <div className="mb-4 flex-1 space-y-4 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-gray-500">
            Try: &quot;Which creators get the most engagement?&quot; or &quot;Would reus.fx fit
            a skincare brand?&quot;
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-lg px-4 py-2 ${
                m.role === "user" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-900"
              }`}
            >
              {m.role === "assistant" && m.kind && (
                <span
                  className={`mb-1 inline-block rounded px-2 py-0.5 text-xs font-medium ${KIND_STYLE[m.kind]}`}
                >
                  {KIND_LABEL[m.kind]}
                </span>
              )}
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.sources && m.sources.length > 0 && (
                <details className="mt-2 text-xs text-gray-600">
                  <summary className="cursor-pointer select-none">
                    Data used ({m.sources.length})
                  </summary>
                  <div className="mt-1 space-y-1">
                    {m.sources.map((s, si) => (
                      <pre
                        key={si}
                        className="overflow-x-auto rounded bg-gray-50 p-2 text-[11px] whitespace-pre-wrap"
                      >
                        {s.tool}({JSON.stringify(s.input)}) &rarr;{"\n"}
                        {JSON.stringify(s.output, null, 2)}
                      </pre>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-gray-500">Thinking&hellip;</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the creators…"
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-gray-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </main>
  );
}
