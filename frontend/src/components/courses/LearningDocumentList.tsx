import type { KnowledgeDocument } from "@/types/learning";

export function LearningDocumentList({ documents }: { documents: KnowledgeDocument[] }) {
  return (
    <ul className="mt-3 divide-y divide-slate-100">
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
  );
}
