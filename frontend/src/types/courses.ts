/** Course records the learning API may return. This app does not create courses locally. */

export type Course = {
  id: string;
  title: string;
  description: string;
  /** Null when the response does not include knowledge-base document ids. */
  document_ids: string[] | null;
};

export type CourseDraft = {
  title: string;
  description: string;
};
