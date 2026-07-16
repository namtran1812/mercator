export interface BondPrice {
  instrument_id: number;
  clean_price: number;
  dirty_price: number;
  yield_to_maturity: number;
  g_spread_bps: number;
  modified_duration: number;
  quality_score: number;
  quality_status: string;
  curve_version: number;
  reference_version: number;
}

export interface ClientBrief {
  issuer_name: string;
  question: string;
  summary: string;
  market_observations: string[];
  evidence_summary: string[];
  risks: string[];
  citations: string[];
}
