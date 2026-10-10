export type HealthStatus = {
  status: string;
  database: string;
};

export type KnowledgeDocument = {
  id: string;
  filename: string;
  title: string;
  file_type: string;
  total_pages: number;
  total_chunks: number;
  processing_status: string;
  created_at: string;
};

export type KnowledgeDocumentList = {
  documents: KnowledgeDocument[];
};

export type DocumentUploadResult = {
  document_id: string;
  filename: string;
  total_pages: number;
  total_chunks: number;
  processing_status: string;
};

export type TutorSource = {
  document_id: string;
  document_name: string;
  page_number: number;
  chunk_id: string;
  similarity: number;
};

export type TutorReply = {
  answer: string;
  sources: TutorSource[];
};

export type Student = {
  id: string;
  name: string;
  created_at: string;
};

export type TopicProgress = {
  topic: string;
  mastery: number;
  questions_attempted: number;
  questions_correct: number;
};

export type StudentProgress = {
  student_id: string;
  topics: TopicProgress[];
};

export type LearningGap = {
  topic: string;
  mastery: number;
  severity: string;
  reason: string;
  status: string;
  detected_at: string;
};

export type StudentLearningGaps = {
  student_id: string;
  learning_gaps: LearningGap[];
};

export type PublicQuestion = {
  id: string;
  question_text: string;
  question_type: string;
  topic: string;
  difficulty: string;
  options: Record<string, string>;
  source_document_name: string | null;
  source_page_number: number | null;
};

export type Assessment = {
  id: string;
  title: string;
  description: string;
  topic: string;
  questions: PublicQuestion[];
};

export type AssessmentGeneration = {
  status: "created" | "no_context";
  message: string | null;
  assessment: Assessment | null;
};

export type TopicResult = {
  topic: string;
  correct: number;
  attempted: number;
  mastery: number;
};

export type AssessmentResult = {
  attempt_id: string;
  score: number;
  total_questions: number;
  percentage: number;
  topic_results: TopicResult[];
  learning_gaps: LearningGap[];
};

/** Shape for a future assessment-history API. The current backend does not return this list. */
export type AssessmentHistoryItem = {
  id: string;
  title: string;
  topic: string;
  percentage: number;
  completedAt: string;
};

/** Shape for a future mastery-history API. The current backend stores only the latest score per topic. */
export type MasteryPoint = {
  label: string;
  mastery: number;
};
