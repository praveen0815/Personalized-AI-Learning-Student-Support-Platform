"use client";

import { LearningGaps } from "@/components/dashboard/LearningGaps";
import { LearningProgressChart } from "@/components/dashboard/LearningProgressChart";
import { RecommendedActions } from "@/components/dashboard/RecommendedActions";
import { RecentAssessments } from "@/components/dashboard/RecentAssessments";
import { StatCard } from "@/components/dashboard/StatCard";
import { TopicMastery } from "@/components/dashboard/TopicMastery";
import { TutorCTA } from "@/components/dashboard/TutorCTA";
import { WelcomeHeader } from "@/components/dashboard/WelcomeHeader";
import { PageTitle } from "@/components/layout/PageTitle";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useDashboardData } from "@/hooks/useDashboardData";
import { averageMastery, questionsAttempted } from "@/lib/mastery";

export function DashboardScreen() {
  const dashboard = useDashboardData();
  const topics = dashboard.progress.status === "ready" ? dashboard.progress.data : [];
  const gaps = dashboard.gaps.status === "ready" ? dashboard.gaps.data : [];
  const mastery = dashboard.progress.status === "ready" ? averageMastery(topics) : null;
  const showSetup = !dashboard.studentId;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
      <PageTitle title="Dashboard" />
      <WelcomeHeader />
      {showSetup ? (
        <Card>
          <h2 className="text-card-title text-slate-900">Student record not connected</h2>
          <p className="mt-1 text-secondary text-slate-500">
            Set NEXT_PUBLIC_DEMO_STUDENT_ID, or create one development student. The same id is kept in this browser
            and is not created again on later visits.
          </p>
          <Button className="mt-4" onClick={() => void dashboard.createDevelopmentStudent()} disabled={dashboard.creating}>
            {dashboard.creating ? "Creating student" : "Create development student"}
          </Button>
          {dashboard.createError ? <p className="mt-2 text-secondary text-rose-700">{dashboard.createError}</p> : null}
        </Card>
      ) : null}
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Learning summary">
        {dashboard.progress.status === "loading" ? (
          <>
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </>
        ) : dashboard.progress.status === "error" ? (
          <>
            <StatCard label="Overall mastery" value="—" supporting="Unable to load learning progress" />
            <StatCard label="Topics tracked" value="—" supporting="Unable to load learning progress" />
            <StatCard label="Questions attempted" value="—" supporting="Unable to load learning progress" />
          </>
        ) : (
          <>
            <StatCard
              label="Overall mastery"
              value={mastery === null ? "—" : `${mastery}%`}
              supporting={
                mastery === null ? "No topics yet" : "Average of topic scores returned by the API"
              }
            />
            <StatCard
              label="Topics tracked"
              value={dashboard.progress.status === "ready" ? String(topics.length) : "—"}
              supporting="Active learning topics"
            />
            <StatCard
              label="Questions attempted"
              value={dashboard.progress.status === "ready" ? String(questionsAttempted(topics)) : "—"}
              supporting="Sum of topic attempt counts"
            />
          </>
        )}
        {dashboard.gaps.status === "loading" ? (
          <Skeleton className="h-20" />
        ) : dashboard.gaps.status === "error" ? (
          <StatCard label="Current learning gaps" value="—" supporting="Unable to load learning gaps" />
        ) : (
          <StatCard
            label="Current learning gaps"
            value={dashboard.gaps.status === "ready" ? String(gaps.length) : "—"}
            supporting="Active gaps from the API"
          />
        )}
      </section>
      <section className="grid gap-3 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <LearningProgressChart
            points={[]}
            emptyMessage="The progress API returns the latest mastery for each topic, not a dated history."
          />
        </div>
        <TutorCTA />
      </section>
      <section className="grid gap-3 lg:grid-cols-2">
        <TopicMastery
          topics={topics}
          status={dashboard.progress.status}
          message={dashboard.progress.status === "error" ? dashboard.progress.message : undefined}
          onRetry={dashboard.reloadProgress}
        />
        <LearningGaps
          gaps={gaps}
          status={dashboard.gaps.status}
          message={dashboard.gaps.status === "error" ? dashboard.gaps.message : undefined}
          onRetry={dashboard.reloadGaps}
        />
      </section>
      <RecommendedActions
        gaps={gaps}
        topics={topics}
        progressStatus={dashboard.progress.status}
        gapsStatus={dashboard.gaps.status}
        progressMessage={dashboard.progress.status === "error" ? dashboard.progress.message : undefined}
        gapsMessage={dashboard.gaps.status === "error" ? dashboard.gaps.message : undefined}
        onRetry={() => {
          dashboard.reloadProgress();
          dashboard.reloadGaps();
        }}
      />
      <RecentAssessments items={[]} historyAvailable={false} />
    </div>
  );
}
