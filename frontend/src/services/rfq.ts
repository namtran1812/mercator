import { rfqApi } from "./api";
import type {
  ExecutionResponse,
  LiveAccountRisk,
  Rfq,
  RfqDetail,
  RfqRequest,
} from "../types/bond";

export const DEMO_ACCOUNT_ID =
  "00000000-0000-0000-0000-000000000101";

export async function fetchLiveAccountRisk():
Promise<LiveAccountRisk> {
  const response =
    await rfqApi.get<LiveAccountRisk>(
      `/accounts/${DEMO_ACCOUNT_ID}/risk`,
    );

  return response.data;
}

export async function createRfq(
  request: RfqRequest,
): Promise<Rfq> {
  const response = await rfqApi.post<Rfq>(
    "/rfqs",
    request,
  );

  return response.data;
}

export async function fetchRfq(
  rfqId: string,
): Promise<RfqDetail> {
  const response = await rfqApi.get<RfqDetail>(
    `/rfqs/${rfqId}`,
  );

  return response.data;
}

export async function executeRfqQuote(
  rfqId: string,
  quoteId: string,
): Promise<ExecutionResponse> {
  const response =
    await rfqApi.post<ExecutionResponse>(
      `/rfqs/${rfqId}/execute`,
      {
        quote_id: quoteId,
      },
    );

  return response.data;
}

export async function fetchRfqAnalytics():
Promise<
  import("../types/bond").RfqAnalyticsSummary
> {
  const response = await rfqApi.get<
    import("../types/bond").RfqAnalyticsSummary
  >("/analytics/summary");

  return response.data;
}
