"use client";

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Library } from "lucide-react";
import { PageTitle } from "@/components/layout/PageTitle";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { listDocuments, uploadDocument } from "@/lib/api/knowledge";
import { getApiBaseUrl } from "@/lib/env";
import type { DocumentUploadResult, KnowledgeDocument } from "@/types/learning";

function isUploadResult(value: DocumentUploadResult): boolean {
  return (
    typeof value?.document_id === "string" &&
    typeof value.filename === "string" &&
    typeof value.total_pages === "number" &&
    typeof value.total_chunks === "number" &&
    typeof value.processing_status === "string"
  );
}

export function KnowledgeScreen() {
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [message, setMessage] = useState("Unable to load learning materials.");
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [uploadError, setUploadError] = useState("");
  const [uploaded, setUploaded] = useState<DocumentUploadResult | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const response = await listDocuments();
      setDocuments(response.documents);
      setStatus("ready");
    } catch (error) {
      setMessage(error instanceof ApiError ? "Unable to load learning materials." : "Unable to load learning materials.");
      setStatus("error");
    }
  }, []);

  const refresh = useCallback(async () => {
    const response = await listDocuments();
    setDocuments(response.documents);
    setStatus("ready");
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || uploadState === "uploading") {
      return;
    }
    const form = event.currentTarget;
    setUploadState("uploading");
    setUploadError("");
    setUploaded(null);
    try {
      const result = await uploadDocument(file);
      if (!isUploadResult(result)) {
        throw new ApiError("The learning API returned an unexpected upload response.", 200);
      }
      setUploaded(result);
      setUploadState("success");
      setFile(null);
      form.reset();
    } catch (error) {
      setUploadState("error");
      setUploadError(error instanceof ApiError ? error.message : "The document could not be uploaded.");
      return;
    }
    try {
      await refresh();
    } catch (error) {
      setMessage(error instanceof ApiError ? "Unable to load learning materials." : "Unable to load learning materials.");
      setStatus("error");
    }
  }

  return (
    <div className="mx-auto w-full max-w-5xl">
      <PageTitle title="Knowledge Base" />
      <Card>
        <Library className="h-5 w-5 text-indigo-700" aria-hidden="true" />
        <h2 className="mt-3 text-page-title text-slate-900">Knowledge Base</h2>
        <p className="mt-1 text-secondary text-slate-500">
          Uploaded documents are used by the tutor and by assessments.
        </p>
        {status === "loading" ? <Skeleton className="mt-3 h-16" /> : null}
        {status === "error" ? <ErrorState message={message} onRetry={() => void load()} /> : null}
        {status === "ready" && documents.length === 0 ? (
          <EmptyState
            icon={Library}
            title="No learning materials available yet."
            message="Upload a PDF to begin."
          />
        ) : null}
        {status === "ready" && documents.length > 0 ? (
          <ul className="mt-4 divide-y divide-slate-100">
            {documents.map((document) => (
              <li key={document.id} className="py-2">
                <p className="text-body font-medium text-slate-900">{document.filename}</p>
                <p className="font-mono text-meta text-slate-500">
                  {document.file_type.toUpperCase()} · {document.total_pages} pages · {document.total_chunks} chunks ·{" "}
                  {document.processing_status}
                </p>
                <p className="break-all font-mono text-meta text-slate-400">{document.id}</p>
              </li>
            ))}
          </ul>
        ) : null}

        <form className="mt-4 border-t border-slate-100 pt-3" onSubmit={(event) => void onUpload(event)}>
          <label htmlFor="knowledge-pdf" className="text-label text-slate-500 uppercase">
            Upload PDF
          </label>
          <input
            id="knowledge-pdf"
            name="file"
            type="file"
            accept="application/pdf,.pdf"
            disabled={uploadState === "uploading"}
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setUploadState("idle");
              setUploadError("");
              setUploaded(null);
            }}
            className="mt-2 block w-full text-body text-slate-700 file:mr-3 file:h-[34px] file:rounded-md file:border file:border-slate-200 file:bg-white file:px-3.5 file:text-button file:text-slate-900"
          />
          <div className="mt-2 flex items-center justify-between gap-3">
            <p className="text-meta text-slate-500">One PDF per upload.</p>
            <Button type="submit" disabled={uploadState === "uploading" || file === null}>
              {uploadState === "uploading" ? "Uploading" : "Upload"}
            </Button>
          </div>
          {uploadState === "uploading" ? (
            <p className="mt-2 text-secondary text-slate-500" role="status">
              Uploading the PDF…
            </p>
          ) : null}
          {uploadState === "success" && uploaded ? (
            <div className="mt-2" role="status">
              <p className="text-secondary text-emerald-800">Uploaded {uploaded.filename}</p>
              <p className="font-mono text-meta text-slate-500">
                {uploaded.total_pages} pages · {uploaded.total_chunks} chunks · {uploaded.processing_status}
              </p>
            </div>
          ) : null}
          {uploadState === "error" ? (
            <p className="mt-2 text-secondary text-rose-700" role="alert">
              {uploadError}
            </p>
          ) : null}
        </form>

        <ButtonLink className="mt-4" href={`${getApiBaseUrl()}/docs`} variant="secondary">
          Open API docs
        </ButtonLink>
      </Card>
    </div>
  );
}
