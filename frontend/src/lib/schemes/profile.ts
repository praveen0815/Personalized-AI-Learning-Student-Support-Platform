/** Request vocabulary for POST /api/v1/recommend. Values are the predictor's field names, not eligibility rules. */

export const GENDER_OPTIONS = [
  { value: "female", label: "Female" },
  { value: "male", label: "Male" },
  { value: "transgender", label: "Transgender" },
] as const;

export const SCHOOL_OPTIONS = [
  { value: "government_6_to_12", label: "Government school, classes 6 to 12" },
  {
    value: "government_or_aided_tamil_medium_6_to_12",
    label: "Government or aided Tamil-medium school, classes 6 to 12",
  },
  { value: "other", label: "Other" },
] as const;

export const MARITAL_OPTIONS = [
  { value: "never_married", label: "Never married" },
  { value: "married", label: "Married" },
  { value: "widow", label: "Widow" },
  { value: "widow_remarrying", label: "Widow remarrying" },
] as const;

export const OCCUPATION_OPTIONS = [
  { value: "small_marginal_farmer", label: "Small or marginal farmer" },
  { value: "agricultural_labourer", label: "Agricultural labourer" },
  { value: "inland_fishing", label: "Inland fishing" },
  { value: "plantation_labourer", label: "Plantation labourer" },
  { value: "other", label: "Other" },
] as const;

export const YES_NO_OPTIONS = [
  { value: "true", label: "Yes" },
  { value: "false", label: "No" },
] as const;

export type SchemeProfile = {
  age: number;
  gender: (typeof GENDER_OPTIONS)[number]["value"];
  is_student: boolean;
  first_higher_education_course: boolean;
  school_background: (typeof SCHOOL_OPTIONS)[number]["value"];
  marital_status: (typeof MARITAL_OPTIONS)[number]["value"];
  is_orphan: boolean;
  is_destitute: boolean;
  occupation_category: (typeof OCCUPATION_OPTIONS)[number]["value"];
  wet_land_acres: number;
  dry_land_acres: number;
};

export type ProfileDraft = {
  age: string;
  gender: string;
  is_student: string;
  first_higher_education_course: string;
  school_background: string;
  marital_status: string;
  is_orphan: string;
  is_destitute: string;
  occupation_category: string;
  wet_land_acres: string;
  dry_land_acres: string;
};

export function emptyProfileDraft(): ProfileDraft {
  return {
    age: "",
    gender: "",
    is_student: "",
    first_higher_education_course: "",
    school_background: "",
    marital_status: "",
    is_orphan: "",
    is_destitute: "",
    occupation_category: "",
    wet_land_acres: "",
    dry_land_acres: "",
  };
}

function optionValues(options: readonly { value: string }[]): string[] {
  return options.map((option) => option.value);
}

function choiceError(value: string, allowed: readonly string[], label: string): string | null {
  if (!value.trim()) {
    return `Select ${label}.`;
  }
  if (!allowed.includes(value)) {
    return `Select a valid ${label}.`;
  }
  return null;
}

function landError(value: string, label: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return `Enter ${label}.`;
  }
  const acres = Number(trimmed);
  if (!Number.isFinite(acres)) {
    return `${label} must be a number.`;
  }
  if (acres < 0) {
    return `${label} must be 0 or greater.`;
  }
  return null;
}

export function validateProfile(draft: ProfileDraft): { ok: true; profile: SchemeProfile } | { ok: false; errors: string[] } {
  const errors: string[] = [];
  const ageText = draft.age.trim();
  let age = Number.NaN;
  if (!ageText) {
    errors.push("Enter age.");
  } else if (!/^\d+$/.test(ageText)) {
    errors.push("Age must be a whole number from 0 to 120.");
  } else {
    age = Number(ageText);
    if (age > 120) {
      errors.push("Age must be a whole number from 0 to 120.");
    }
  }

  const genderError = choiceError(draft.gender, optionValues(GENDER_OPTIONS), "gender");
  const studentError = choiceError(draft.is_student, optionValues(YES_NO_OPTIONS), "whether the student is currently a student");
  const courseError = choiceError(
    draft.first_higher_education_course,
    optionValues(YES_NO_OPTIONS),
    "whether this is the first higher-education course",
  );
  const schoolError = choiceError(draft.school_background, optionValues(SCHOOL_OPTIONS), "school background");
  const maritalError = choiceError(draft.marital_status, optionValues(MARITAL_OPTIONS), "marital status");
  const orphanError = choiceError(draft.is_orphan, optionValues(YES_NO_OPTIONS), "whether the student is an orphan");
  const destituteError = choiceError(draft.is_destitute, optionValues(YES_NO_OPTIONS), "whether the student is destitute");
  const occupationError = choiceError(draft.occupation_category, optionValues(OCCUPATION_OPTIONS), "occupation");
  const wetError = landError(draft.wet_land_acres, "Wet land in acres");
  const dryError = landError(draft.dry_land_acres, "Dry land in acres");

  for (const error of [
    genderError,
    studentError,
    courseError,
    schoolError,
    maritalError,
    orphanError,
    destituteError,
    occupationError,
    wetError,
    dryError,
  ]) {
    if (error) {
      errors.push(error);
    }
  }

  if (errors.length > 0 || !Number.isInteger(age)) {
    return { ok: false, errors };
  }

  return {
    ok: true,
    profile: {
      age,
      gender: draft.gender as SchemeProfile["gender"],
      is_student: draft.is_student === "true",
      first_higher_education_course: draft.first_higher_education_course === "true",
      school_background: draft.school_background as SchemeProfile["school_background"],
      marital_status: draft.marital_status as SchemeProfile["marital_status"],
      is_orphan: draft.is_orphan === "true",
      is_destitute: draft.is_destitute === "true",
      occupation_category: draft.occupation_category as SchemeProfile["occupation_category"],
      wet_land_acres: Number(draft.wet_land_acres.trim()),
      dry_land_acres: Number(draft.dry_land_acres.trim()),
    },
  };
}
