import { agentApi } from "./api";

import type {
  AgentQueryResponse,
} from "../types/bond";


export interface AgentQueryRequest {
  question: string;
  instrument_ids: number[];
  maximum_evidence?: number;
}


export async function queryAgent(
  request: AgentQueryRequest,
): Promise<AgentQueryResponse> {
  const response =
    await agentApi.post<AgentQueryResponse>(
      "/agent/query",
      {
        ...request,

        maximum_evidence:
          request.maximum_evidence ?? 5,
      },
    );

  return response.data;
}
