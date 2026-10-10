import type { Metadata } from "next";
import { CourseDetailScreen } from "@/components/courses/CourseDetailScreen";

export const metadata: Metadata = { title: "Course" };

export default async function CoursePage({ params }: { params: Promise<{ courseId: string }> }) {
  const { courseId } = await params;
  return <CourseDetailScreen courseId={courseId} />;
}
