import { marketApi } from "./api";
import type { BondPrice } from "../types/bond";

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
