/** Response shapes from the existing scheme predictor. This app does not score eligibility. */

export type SchemeRuleResult = {
  eligible: boolean;
  reasons: string[];
  rule_status?: string | null;
  verification_notes?: string | null;
};

export type RecommendedScheme = {
  scheme_id: string;
  scheme_name: string;
  prediction: string;
  status_label: string;
  eligible_probability: number;
  not_eligible_probability: number;
  reason: string;
  department?: string | null;
  scheme_category?: string | null;
  description?: string | null;
  benefit?: string | null;
  required_documents?: string | null;
  application_method?: string | null;
  official_source_url?: string | null;
  rule_result?: SchemeRuleResult | null;
  rule_reasons?: string[];
  ml_prediction?: string;
  agreement?: boolean;
};

export type EvaluatedScheme = {
  scheme_id: string;
  scheme_name: string;
  prediction: string;
  eligible_probability: number;
  not_eligible_probability: number;
  reason: string;
  rule_eligible: boolean;
  ml_prediction: string;
  agreement: boolean;
};

export type RecommendResponse = {
  total_schemes_evaluated: number;
  eligible_scheme_count: number;
  ranking_rule: string;
  recommendations: RecommendedScheme[];
  evaluated_schemes: EvaluatedScheme[];
  disclaimer: string;
};
