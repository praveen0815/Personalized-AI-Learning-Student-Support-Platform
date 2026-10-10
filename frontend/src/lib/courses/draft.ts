import type { CourseDraft } from "@/types/courses";

const TITLE_MAX = 200;
const DESCRIPTION_MAX = 2000;

export function validateCourseDraft(
  title: string,
  description: string,
): { ok: true; draft: CourseDraft } | { ok: false; errors: string[] } {
  const errors: string[] = [];
  const trimmedTitle = title.trim();
  const trimmedDescription = description.trim();
  if (!trimmedTitle) {
    errors.push("Enter a title.");
  } else if (trimmedTitle.length > TITLE_MAX) {
    errors.push("Title must be 200 characters or fewer.");
  }
  if (!trimmedDescription) {
    errors.push("Enter a description.");
  } else if (trimmedDescription.length > DESCRIPTION_MAX) {
    errors.push("Description must be 2000 characters or fewer.");
  }
  if (errors.length > 0) {
    return { ok: false, errors };
  }
  return { ok: true, draft: { title: trimmedTitle, description: trimmedDescription } };
}
