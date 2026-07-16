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

export interface LivePositionRisk {
  account_id: string;
  instrument_id: number;
  face_value: number;
  average_cost: number;
  current_clean_price: number;
  cost_basis: number;
  market_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_pnl: number;
  yield_to_maturity: number;
  g_spread_bps: number;
  modified_duration: number;
  convexity: number;
  dv01: number;
  quality_status: string;
  curve_version: number;
  reference_version: number;
}

export interface LiveAccountRisk {
  account_id: string;
  account_name: string;
  cash_balance: number;
  position_count: number;
  total_face_value: number;
  total_cost_basis: number;
  total_market_value: number;
  total_unrealized_pnl: number;
  total_realized_pnl: number;
  total_pnl: number;
  weighted_yield_to_maturity: number;
  weighted_g_spread_bps: number;
  weighted_modified_duration: number;
  weighted_convexity: number;
  total_dv01: number;
  net_liquidation_value: number;
  positions: LivePositionRisk[];
}

export type RfqSide = "BUY" | "SELL";

export interface RfqRequest {
  account_id: string;
  instrument_id: number;
  side: RfqSide;
  quantity: number;
  client: string;
}

export interface Rfq {
  id: string;
  account_id: string;
  instrument_id: number;
  side: RfqSide;
  quantity: number;
  client: string;
  requested_at: string;
  status:
    | "REQUESTED"
    | "QUOTING"
    | "QUOTED"
    | "EXECUTED"
    | "CANCELLED"
    | "EXPIRED";
}

export interface DealerQuote {
  id: string;
  rfq_id: string;
  dealer: string;
  price: number;
  spread_bps: number;
  latency_ms: number;
  inventory_adjustment_bps: number;
  size_adjustment_bps: number;
  quoted_at: string;
  expires_at: string | null;
  quote_status:
    | "ACTIVE"
    | "EXECUTED"
    | "REJECTED"
    | "EXPIRED";
}

export interface RfqDetail {
  rfq: Rfq;
  quotes: DealerQuote[];
}

export interface Execution {
  id: string;
  rfq_id: string;
  quote_id: string;
  account_id: string;
  instrument_id: number;
  side: RfqSide;
  client: string;
  dealer: string;
  price: number;
  quantity: number;
  executed_at: string;
  execution_status: string;
}

export interface ExecutionResponse {
  execution: Execution;
  rejected_quote_count: number;
}

export interface DealerAnalytics {
  dealer: string;
  quote_count: number;
  execution_count: number;
  hit_ratio: number;
  average_latency_ms: number;
  average_spread_bps: number;
  average_price: number;
}

export interface RfqAnalyticsSummary {
  rfq_count: number;
  quoted_rfq_count: number;
  executed_rfq_count: number;
  execution_rate: number;
  average_quotes_per_rfq: number;
  average_dealer_latency_ms: number;
  p95_dealer_latency_ms: number;
  average_execution_latency_ms: number;
  total_notional: number;
  executed_notional: number;
  dealers: DealerAnalytics[];
}

export interface RelativeValueOpportunity {
  instrument_id: number;
  clean_price: number;
  yield_to_maturity: number;
  g_spread_bps: number;
  modified_duration: number;
  peer_count: number;
  peer_average_spread_bps: number;
  peer_spread_standard_deviation_bps: number;
  spread_difference_bps: number;
  spread_z_score: number;
  duration_adjusted_spread: number;
  classification: "CHEAP" | "RICH" | "FAIR";
  conviction_score: number;
}

export interface RelativeValueResponse {
  instrument_count: number;
  opportunity_count: number;
  average_spread_bps: number;
  average_duration: number;
  opportunities: RelativeValueOpportunity[];
}
