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

export interface PriceHistoryPoint {
  event_time: string;
  clean_price: number;
  dirty_price: number;
  yield_to_maturity: number;
  g_spread_bps: number;
  modified_duration: number;
  convexity: number;
  quality_score: number;
  quality_status: string;
  curve_version: number;
  reference_version: number;
  model_version: string;
  calculation_trace_id: string;
  source_event_id: string;
}

export interface ScenarioRequest {
  instrument_ids: number[];
  treasury_shock_bps: number;
  credit_spread_shock_bps: number;
  position_face_value: number;
}

export interface ScenarioResult {
  instrument_id: number;
  base_clean_price: number;
  shocked_clean_price: number;
  price_change: number;
  price_change_percent: number;
  base_yield: number;
  shocked_yield: number;
  base_spread_bps: number;
  shocked_spread_bps: number;
  modified_duration: number;
  convexity: number;
  estimated_pnl: number;
}

export interface ScenarioResponse {
  treasury_shock_bps: number;
  credit_spread_shock_bps: number;
  position_face_value: number;
  instrument_count: number;
  total_estimated_pnl: number;
  results: ScenarioResult[];
}

export interface PortfolioPosition {
  instrument_id: number;
  face_value: number;
}

export interface PositionRisk {
  instrument_id: number;
  face_value: number;
  clean_price: number;
  market_value: number;
  yield_to_maturity: number;
  g_spread_bps: number;
  modified_duration: number;
  convexity: number;
  dv01: number;
  convexity_contribution: number;
  market_value_weight: number;
}

export interface PortfolioRiskResponse {
  position_count: number;
  total_face_value: number;
  total_market_value: number;
  weighted_yield_to_maturity: number;
  weighted_g_spread_bps: number;
  weighted_modified_duration: number;
  weighted_convexity: number;
  total_dv01: number;
  total_convexity_contribution: number;
  positions: PositionRisk[];
}

export interface ReplayScenario {
  scenario_name: string;
  event_count: number;
  first_event_time: string;
  last_event_time: string;
}
