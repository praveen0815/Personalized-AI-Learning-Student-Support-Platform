import { apiGet, apiPostForm } from "@/lib/api/client";
import type { DocumentUploadResult, KnowledgeDocumentList } from "@/types/learning";

export function listDocuments(): Promise<KnowledgeDocumentList> {
  return apiGet<KnowledgeDocumentList>("/api/v1/knowledge/documents");
}

function uploadErrorMessage(status: number, detail: string | null): string {
  if (detail) {
    return detail;
  }
  if (status === 0) {
    return "Unable to reach the learning API.";
  }
  if (status === 413) {
    return "The file is too large to upload.";
  }
  if (status === 400 || status === 422) {
    return "The file could not be uploaded. Choose a PDF.";
  }
  return "The document could not be uploaded.";
}

export function uploadDocument(file: File): Promise<DocumentUploadResult> {
  const body = new FormData();
  body.append("file", file);
  return apiPostForm<DocumentUploadResult>("/api/v1/knowledge/documents", body, uploadErrorMessage);
}
