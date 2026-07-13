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

export type SldNodeClass =
  | "transformer"
  | "breaker"
  | "ats"
  | "ups"
  | "generator"
  | "busbar"
  | "it_load";

export type SLDNode = {
  node_id: string;
  node_class: SldNodeClass | string;
  bbox: [number, number, number, number];
  confidence: number;
  tag: string | null;
};

export type SLDEdge = {
  source_node_id: string;
  target_node_id: string;
  confidence: number;
};

export type RedundancyResult = {
  source_doc: string;
  claimed_redundancy: string;
  holds: boolean;
  reason: string;
  failure_paths: string[][];
  spof_node_id: string | null;
  traced_paths: string[][];
};

export type GraphNodeType = "spec" | "equipment" | "vendor" | "shipment" | "task";
export type GraphRelation = "REQUIRES" | "SUBMITTED_BY" | "DELIVERS" | "BLOCKS" | "PRECEDES";

export type GraphNode = {
  node_id: string;
  node_type: GraphNodeType;
  label: string;
};

export type GraphEdge = {
  source: string;
  target: string;
  relation: GraphRelation;
};

export type GraphResult = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type TraversalResult = {
  start_node_id: string | null;
  path_node_ids: string[];
  nodes: GraphNode[];
  edges: GraphEdge[];
  reason: string;
};

export type SldTopologyResult = {
  topology_id: string;
  name: string;
  image_path: string;
  nodes: SLDNode[];
  edges: SLDEdge[];
  redundancy: RedundancyResult;
};
