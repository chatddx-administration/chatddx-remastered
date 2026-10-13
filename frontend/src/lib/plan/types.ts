// The answer of a configuration whose output is worlds/sample/_data/schemas/management_plan_v1.json, read
// defensively: an answer that breaks its schema, or was cut short, is shown as far as it goes.
export const PLAN = "management_plan_v1";

export type Probability = "high" | "medium" | "low";
export type Priority = "urgent" | "prompt" | "elective";

export interface Diagnosis {
  diagnosis?: string;
  probability?: Probability;
  critical?: boolean;
  short_rationale?: string;
}

export interface WorkupItem {
  type?: string;
  investigations?: string[];
  priority?: Priority;
}

export interface Treatment {
  indication?: string;
  treatment?: string;
  important?: string;
}

export interface Management {
  workup?: WorkupItem[];
  empirical_treatment?: Treatment[];
  disposition?: string;
}

export interface ManagementPlan {
  acute_warning?: string | null;
  diagnoses?: Diagnosis[];
  management?: Management;
  sources?: string[];
}

export function isPlan(value: unknown): value is ManagementPlan {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
