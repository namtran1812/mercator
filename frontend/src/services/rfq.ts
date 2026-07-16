import { rfqApi } from "./api";
import type {
  LiveAccountRisk,
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
