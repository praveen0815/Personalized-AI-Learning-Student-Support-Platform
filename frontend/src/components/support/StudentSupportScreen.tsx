"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { AlertCircle, BookOpen, HandHeart } from "lucide-react";
import { PageTitle } from "@/components/layout/PageTitle";
import { Badge } from "@/components/ui/Badge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { recommendSchemes } from "@/lib/schemes/client";
import {
  emptyProfileDraft,
  GENDER_OPTIONS,
  MARITAL_OPTIONS,
  OCCUPATION_OPTIONS,
  SCHOOL_OPTIONS,
  validateProfile,
  YES_NO_OPTIONS,
  type ProfileDraft,
  type SchemeProfile,
} from "@/lib/schemes/profile";
import type { EvaluatedScheme, RecommendResponse, RecommendedScheme } from "@/types/schemes";

const fieldClass =
  "mt-1 h-9 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-body text-slate-900 focus-visible:border-indigo-600 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 disabled:opacity-60";

function formatProbability(value: number): string | null {
  return Number.isFinite(value) ? value.toFixed(2) : null;
}

function officialHref(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  return value.startsWith("https://") || value.startsWith("http://") ? value : null;
}

function Detail({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) {
    return null;
  }
  return (
    <p className="mt-1 text-secondary text-slate-600">
      <span className="text-slate-500">{label}: </span>
      {value}
    </p>
  );
}

function SelectField({
  id,
  label,
  value,
  options,
  disabled,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: readonly { value: string; label: string }[];
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label htmlFor={id} className="text-label uppercase text-slate-500">
        {label}
      </label>
      <select id={id} className={fieldClass} value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function EligibleSchemeCard({ scheme }: { scheme: RecommendedScheme }) {
  const source = officialHref(scheme.official_source_url);
  const reasons = scheme.rule_result?.reasons?.filter((reason) => reason.trim()) ?? scheme.rule_reasons?.filter((reason) => reason.trim()) ?? [];
  const probability = formatProbability(scheme.eligible_probability);
  return (
    <article className="rounded-md border border-slate-200 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="text-card-title text-slate-900">{scheme.scheme_name}</h4>
        <Badge tone="strong">{scheme.status_label || scheme.prediction}</Badge>
      </div>
      {scheme.scheme_id ? <p className="mt-1 font-mono text-meta text-slate-500">{scheme.scheme_id}</p> : null}
      <Detail label="Reason" value={scheme.reason} />
      {reasons.length > 0 ? <Detail label="Eligibility details" value={reasons.join("; ")} /> : null}
      <Detail label="Rule status" value={scheme.rule_result?.rule_status ?? undefined} />
      <Detail label="Verification notes" value={scheme.rule_result?.verification_notes ?? undefined} />
      <Detail label="Benefit" value={scheme.benefit} />
      <Detail label="Required documents" value={scheme.required_documents} />
      <Detail label="Application method" value={scheme.application_method} />
      {probability ? <Detail label="Eligible probability" value={probability} /> : null}
      <Detail label="Model prediction" value={scheme.ml_prediction} />
      {typeof scheme.agreement === "boolean" ? (
        <Detail label="Rule and model agreement" value={scheme.agreement ? "true" : "false"} />
      ) : null}
      {source ? (
        <a className="mt-1 block truncate text-secondary text-indigo-800 underline" href={source}>
          {source}
        </a>
      ) : (
        <Detail label="Official source" value={scheme.official_source_url} />
      )}
    </article>
  );
}

function EvaluatedSchemeRow({ scheme }: { scheme: EvaluatedScheme }) {
  const probability = formatProbability(scheme.eligible_probability);
  return (
    <article className="rounded-md border border-slate-200 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="text-card-title text-slate-900">{scheme.scheme_name}</h4>
        <Badge tone={scheme.prediction === "eligible" ? "strong" : "attention"}>{scheme.prediction}</Badge>
      </div>
      {scheme.scheme_id ? <p className="mt-1 font-mono text-meta text-slate-500">{scheme.scheme_id}</p> : null}
      <Detail label="Reason" value={scheme.reason} />
      <Detail label="Rule eligible" value={scheme.rule_eligible ? "true" : "false"} />
      {probability ? <Detail label="Eligible probability" value={probability} /> : null}
      <Detail label="Model prediction" value={scheme.ml_prediction} />
      <Detail label="Rule and model agreement" value={scheme.agreement ? "true" : "false"} />
    </article>
  );
}

export function StudentSupportScreen() {
  const [draft, setDraft] = useState<ProfileDraft>(emptyProfileDraft);
  const [errors, setErrors] = useState<string[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [submitted, setSubmitted] = useState<SchemeProfile | null>(null);

  function update(field: keyof ProfileDraft, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  async function check(profile: SchemeProfile) {
    setStatus("loading");
    setMessage("");
    setResult(null);
    setSubmitted(profile);
    try {
      const response = await recommendSchemes(profile);
      setResult(response);
      setStatus("ready");
    } catch (error) {
      setMessage(
        error instanceof ApiError
          ? error.message
          : "The government scheme predictor could not check this profile.",
      );
      setStatus("error");
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validated = validateProfile(draft);
    if (!validated.ok) {
      setErrors(validated.errors);
      setResult(null);
      setStatus("idle");
      setMessage("");
      return;
    }
    setErrors([]);
    void check(validated.profile);
  }

  const eligible = result?.recommendations.filter((scheme) => scheme.scheme_name?.trim()) ?? [];
  const evaluated = result?.evaluated_schemes.filter((scheme) => scheme.scheme_name?.trim()) ?? [];

  return (
    <div className="mx-auto w-full max-w-5xl space-y-5">
      <PageTitle title="Student Support" />
      <div>
        <h2 className="text-page-title text-slate-900">Student Support</h2>
        <p className="mt-1 max-w-2xl text-secondary text-slate-500">
          Learning support and government scheme support are separate. Scheme results come only from the existing eligibility predictor.
        </p>
      </div>

      <Card>
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-indigo-700" aria-hidden="true" />
          <h3 className="text-section text-slate-900">Learning Support</h3>
        </div>
        <p className="mt-2 text-secondary text-slate-500">
          Course questions and practice stay in the tutor and assessments. They do not decide scheme eligibility.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <ButtonLink href="/tutor" variant="secondary">
            AI Tutor
          </ButtonLink>
          <ButtonLink href="/assessments" variant="secondary">
            Assessments
          </ButtonLink>
        </div>
      </Card>

      <Card>
        <div className="flex items-center gap-2">
          <HandHeart className="h-4 w-4 text-indigo-700" aria-hidden="true" />
          <h3 className="text-section text-slate-900">Government Scheme Support</h3>
        </div>
        <p className="mt-2 text-secondary text-slate-500">
          Enter the socio-economic profile the predictor requires. This form does not use learning progress or invent eligibility.
        </p>

        <form id="student-scheme-profile" className="mt-4" onSubmit={onSubmit}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="scheme-age" className="text-label uppercase text-slate-500">
                Age
              </label>
              <input
                id="scheme-age"
                className={fieldClass}
                inputMode="numeric"
                value={draft.age}
                disabled={status === "loading"}
                onChange={(event) => update("age", event.target.value)}
              />
            </div>
            <SelectField
              id="scheme-gender"
              label="Gender"
              value={draft.gender}
              options={GENDER_OPTIONS}
              disabled={status === "loading"}
              onChange={(value) => update("gender", value)}
            />
            <SelectField
              id="scheme-student"
              label="Currently a student"
              value={draft.is_student}
              options={YES_NO_OPTIONS}
              disabled={status === "loading"}
              onChange={(value) => update("is_student", value)}
            />
            <SelectField
              id="scheme-course"
              label="First higher-education course"
              value={draft.first_higher_education_course}
              options={YES_NO_OPTIONS}
              disabled={status === "loading"}
              onChange={(value) => update("first_higher_education_course", value)}
            />
            <SelectField
              id="scheme-school"
              label="School background"
              value={draft.school_background}
              options={SCHOOL_OPTIONS}
              disabled={status === "loading"}
              onChange={(value) => update("school_background", value)}
            />
            <SelectField
              id="scheme-marital"
              label="Marital status"
              value={draft.marital_status}
              options={MARITAL_OPTIONS}
              disabled={status === "loading"}
              onChange={(value) => update("marital_status", value)}
            />
            <SelectField
              id="scheme-orphan"
              label="Orphan"
              value={draft.is_orphan}
              options={YES_NO_OPTIONS}
              disabled={status === "loading"}
              onChange={(value) => update("is_orphan", value)}
            />
            <SelectField
              id="scheme-destitute"
              label="Destitute"
              value={draft.is_destitute}
              options={YES_NO_OPTIONS}
              disabled={status === "loading"}
              onChange={(value) => update("is_destitute", value)}
            />
            <SelectField
              id="scheme-occupation"
              label="Occupation"
              value={draft.occupation_category}
              options={OCCUPATION_OPTIONS}
              disabled={status === "loading"}
              onChange={(value) => update("occupation_category", value)}
            />
            <div>
              <label htmlFor="scheme-wet-land" className="text-label uppercase text-slate-500">
                Wet land (acres)
              </label>
              <input
                id="scheme-wet-land"
                className={fieldClass}
                inputMode="decimal"
                value={draft.wet_land_acres}
                disabled={status === "loading"}
                onChange={(event) => update("wet_land_acres", event.target.value)}
              />
            </div>
            <div>
              <label htmlFor="scheme-dry-land" className="text-label uppercase text-slate-500">
                Dry land (acres)
              </label>
              <input
                id="scheme-dry-land"
                className={fieldClass}
                inputMode="decimal"
                value={draft.dry_land_acres}
                disabled={status === "loading"}
                onChange={(event) => update("dry_land_acres", event.target.value)}
              />
            </div>
          </div>

          {errors.length > 0 ? (
            <ul className="mt-3 space-y-1" role="alert">
              {errors.map((error) => (
                <li key={error} className="text-secondary text-rose-700">
                  {error}
                </li>
              ))}
            </ul>
          ) : null}

          <Button className="mt-4" type="submit" disabled={status === "loading"}>
            {status === "loading" ? "Checking" : "Check eligibility"}
          </Button>
        </form>

        {status === "loading" ? (
          <div className="mt-4 space-y-2" aria-live="polite">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : null}

        {status === "error" ? (
          <div className="mt-4 rounded-lg border border-slate-200 p-4" role="alert">
            <AlertCircle className="h-4 w-4 text-rose-700" aria-hidden="true" />
            <h4 className="mt-2 text-card-title text-slate-900">{message}</h4>
            <p className="mt-1 text-secondary text-slate-500">The learning API was not used for this check.</p>
            {submitted ? (
              <Button className="mt-3" onClick={() => void check(submitted)}>
                Try again
              </Button>
            ) : null}
          </div>
        ) : null}

        {status === "ready" && result ? (
          <div className="mt-4 space-y-3">
            <p className="text-meta text-slate-500">
              {result.eligible_scheme_count} predicted eligible of {result.total_schemes_evaluated} schemes evaluated.
              {result.ranking_rule ? ` Ranking: ${result.ranking_rule}.` : ""}
            </p>
            {eligible.length === 0 ? (
              <EmptyState
                icon={HandHeart}
                title="No eligible schemes"
                message="The predictor did not return any predicted-eligible schemes for this profile."
              />
            ) : (
              <div className="space-y-2">
                {eligible.map((scheme) => (
                  <EligibleSchemeCard key={scheme.scheme_id || scheme.scheme_name} scheme={scheme} />
                ))}
              </div>
            )}
            {evaluated.length > 0 ? (
              <div className="space-y-2">
                <h4 className="text-card-title text-slate-900">All evaluated schemes</h4>
                {evaluated.map((scheme) => (
                  <EvaluatedSchemeRow key={`evaluated-${scheme.scheme_id || scheme.scheme_name}`} scheme={scheme} />
                ))}
              </div>
            ) : null}
            {result.disclaimer ? <p className="text-meta text-slate-500">{result.disclaimer}</p> : null}
          </div>
        ) : null}
      </Card>
    </div>
  );
}
