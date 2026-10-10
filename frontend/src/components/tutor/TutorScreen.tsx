"use client";

import { useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { Bot } from "lucide-react";
import { PageTitle } from "@/components/layout/PageTitle";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ApiError } from "@/lib/api/client";
import { askTutor } from "@/lib/api/tutor";
import type { TutorSource } from "@/types/learning";

type Exchange = {
  id: number;
  question: string;
  status: "loading" | "ready" | "error";
  answer: string | null;
  sources: TutorSource[];
  error: string | null;
};

function formatSimilarity(value: number): string {
  return Number.isFinite(value) ? value.toFixed(3) : "unavailable";
}

function SourceList({ sources }: { sources: TutorSource[] }) {
  if (sources.length === 0) {
    return <p className="mt-2 text-secondary text-slate-500">No sources were returned.</p>;
  }

  return (
    <div className="mt-3 border-t border-slate-100 pt-2">
      <p className="text-label text-slate-500 uppercase">Sources</p>
      <ul className="mt-2 space-y-2">
        {sources.map((source) => (
          <li key={source.chunk_id} className="rounded-md border border-slate-200 px-3 py-2">
            <p className="text-body font-medium text-slate-900">{source.document_name}</p>
            <p className="font-mono text-meta text-slate-500">
              page {source.page_number} · similarity {formatSimilarity(source.similarity)}
            </p>
            <p className="break-all font-mono text-meta text-slate-400">document {source.document_id}</p>
            <p className="break-all font-mono text-meta text-slate-400">chunk {source.chunk_id}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function TutorScreen({ topic }: { topic?: string }) {
  const [draft, setDraft] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const nextId = useRef(1);
  const pending = exchanges.some((item) => item.status === "loading");

  async function send(question: string, existingId?: number) {
    const trimmed = question.trim();
    if (!trimmed || (existingId === undefined && pending)) {
      return;
    }

    const id = existingId ?? nextId.current;
    if (existingId === undefined) {
      nextId.current += 1;
      setExchanges((current) => [
        ...current,
        { id, question: trimmed, status: "loading", answer: null, sources: [], error: null },
      ]);
      setDraft("");
    } else {
      setExchanges((current) =>
        current.map((item) =>
          item.id === id ? { ...item, status: "loading", answer: null, sources: [], error: null } : item,
        ),
      );
    }

    try {
      const reply = await askTutor(trimmed);
      if (typeof reply.answer !== "string" || !Array.isArray(reply.sources)) {
        throw new ApiError("The tutor returned an unexpected response.", 200);
      }
      setExchanges((current) =>
        current.map((item) =>
          item.id === id
            ? { ...item, status: "ready", answer: reply.answer, sources: reply.sources, error: null }
            : item,
        ),
      );
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "The tutor could not answer this question.";
      setExchanges((current) =>
        current.map((item) => (item.id === id ? { ...item, status: "error", error: message } : item)),
      );
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void send(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send(draft);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-[820px] flex-col gap-5">
      <PageTitle title="AI Tutor" />
      <div>
        <h2 className="text-page-title text-slate-900">AI Tutor</h2>
        <p className="mt-1 text-secondary text-slate-500">
          Answers come from your uploaded learning material.
        </p>
        {topic ? <p className="mt-1 font-mono text-meta text-slate-500">Topic {topic}</p> : null}
      </div>

      <Card className="flex flex-col">
        <div className="max-h-[32rem] space-y-4 overflow-y-auto" aria-live="polite">
          {exchanges.length === 0 ? (
            <EmptyState
              icon={Bot}
              title="No questions yet"
              message="Ask a question about your uploaded learning material."
            />
          ) : null}
          {exchanges.map((exchange) => (
            <article key={exchange.id} className="border-b border-slate-100 pb-3 last:border-b-0">
              <p className="text-label text-slate-500 uppercase">Question</p>
              <p className="mt-1 text-body whitespace-pre-wrap text-slate-900">{exchange.question}</p>
              <p className="mt-3 text-label text-slate-500 uppercase">Answer</p>
              {exchange.status === "loading" ? (
                <p className="mt-1 text-secondary text-slate-500" role="status">
                  Waiting for the tutor…
                </p>
              ) : null}
              {exchange.status === "error" && exchange.error ? (
                <div className="mt-1" role="alert">
                  <p className="text-body leading-normal text-rose-700">{exchange.error}</p>
                  <Button
                    className="mt-2"
                    variant="secondary"
                    disabled={pending}
                    onClick={() => void send(exchange.question, exchange.id)}
                  >
                    Try again
                  </Button>
                </div>
              ) : null}
              {exchange.status === "ready" && exchange.answer !== null ? (
                <>
                  <p className="mt-1 text-body leading-[1.5] whitespace-pre-wrap text-slate-800">{exchange.answer}</p>
                  <SourceList sources={exchange.sources} />
                </>
              ) : null}
            </article>
          ))}
        </div>

        <form className="mt-3 border-t border-slate-100 pt-3" onSubmit={onSubmit}>
          <label htmlFor="tutor-question" className="text-label text-slate-500 uppercase">
            Question
          </label>
          <textarea
            id="tutor-question"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder={topic ? `Ask about ${topic}` : "Ask about your uploaded material"}
            rows={3}
            disabled={pending}
            className="mt-1 min-h-20 w-full resize-y rounded-md border border-slate-200 bg-slate-50 px-2.5 py-2 text-body leading-[1.45] text-slate-900 placeholder:text-secondary placeholder:text-slate-400 focus-visible:border-indigo-600 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 disabled:opacity-60"
          />
          <div className="mt-2 flex items-center justify-between gap-3">
            <p className="text-meta text-slate-500">Enter to send. Shift+Enter for a new line.</p>
            <Button type="submit" disabled={pending || draft.trim().length === 0}>
              {pending ? "Sending" : "Send"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
