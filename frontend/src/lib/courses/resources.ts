import type { Course } from "@/types/courses";
import type { KnowledgeDocument } from "@/types/learning";

export type CourseResources = {
  linked: boolean;
  documents: KnowledgeDocument[];
  missingIds: string[];
};

export function resourcesForCourse(course: Course, documents: KnowledgeDocument[]): CourseResources {
  if (course.document_ids === null) {
    return { linked: false, documents: [], missingIds: [] };
  }
  const byId = new Map(documents.map((document) => [document.id, document]));
  const matched: KnowledgeDocument[] = [];
  const missingIds: string[] = [];
  for (const id of course.document_ids) {
    const document = byId.get(id);
    if (document) {
      matched.push(document);
    } else {
      missingIds.push(id);
    }
  }
  return { linked: true, documents: matched, missingIds };
}
