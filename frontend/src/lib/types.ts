export type SourceRegion = {
  source_doc: string;
  source_page: number;
  source_bbox: [number, number, number, number];
};

export type Requirement = {
  req_id: string;
  equipment_class: string;
  parameter: string;
  operator: ">=" | "<=" | "==" | "in" | "!=";
  value: number;
  unit: string;
  condition: string | null;
  source_doc: string;
  source_page: number;
  source_bbox: [number, number, number, number];
};

export type ExtractedValue = {
  equipment_class: string;
  parameter: string;
  value: number;
  unit: string;
  condition: string | null;
  source_doc: string;
  source_page: number;
  source_bbox: [number, number, number, number];
  extraction_confidence: number;
};

export type Verdict = {
  req_id: string;
  status: "PASS" | "NON_CONFORMANCE" | "INSUFFICIENT_DATA";
  required: string;
  submitted: string | null;
  delta_pct: number | null;
  reason: string;
  spec_evidence: SourceRegion;
  submittal_evidence: SourceRegion | null;
};

export type MitigationCandidate = {
  intervention_id: string;
  name: string;
  description: string;
  cost_inr: number;
  baseline_p_slip: number;
  mitigated_p_slip: number;
  delta_p_slip: number;
  efficiency_per_inr: number | null;
  is_zero_cost: boolean;
};
