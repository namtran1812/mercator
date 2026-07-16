import { marketApi } from "./api";
import type {
  BondPrice,
  PriceHistoryPoint,
} from "../types/bond";

export interface MarketSummary {
  instrument_count: number;
  average_clean_price: number;
  average_yield_to_maturity: number;
  average_g_spread_bps: number;
  widest_instrument_id: number | null;
  widest_g_spread_bps: number | null;
}

export async function fetchLatestPrices(
  limit = 100,
): Promise<BondPrice[]> {
  const response = await marketApi.get<BondPrice[]>(
    "/prices/latest",
    {
      params: {
        limit,
        minimum_quality_score: 0.8,
      },
    },
  );

  return response.data;
}

export async function fetchMarketSummary():
Promise<MarketSummary> {
  const response =
    await marketApi.get<MarketSummary>(
      "/market/summary",
    );

  return response.data;
}

export async function fetchPriceHistory(
  instrumentId: number,
  limit = 100,
): Promise<PriceHistoryPoint[]> {
  const response = await marketApi.get<PriceHistoryPoint[]>(
    `/prices/${instrumentId}/history`,
    {
      params: {
        limit,
      },
    },
  );

  return response.data;
}

export async function runScenario(
  request: import("../types/bond").ScenarioRequest,
): Promise<import("../types/bond").ScenarioResponse> {
  const response =
    await marketApi.post<
      import("../types/bond").ScenarioResponse
    >(
      "/scenarios/run",
      request,
    );

  return response.data;
}

export async function fetchPortfolioRisk(
  positions: import("../types/bond").PortfolioPosition[],
): Promise<
  import("../types/bond").PortfolioRiskResponse
> {
  const response = await marketApi.post<
    import("../types/bond").PortfolioRiskResponse
  >(
    "/portfolio/risk",
    {
      positions,
    },
  );

  return response.data;
}

export async function fetchReplayScenarios():
Promise<
  import("../types/bond").ReplayScenario[]
> {
  const response = await marketApi.get<
    import("../types/bond").ReplayScenario[]
  >("/replay/scenarios");

  return response.data;
}
