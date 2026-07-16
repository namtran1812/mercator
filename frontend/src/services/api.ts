import axios from "axios";

export const referenceApi = axios.create({
  baseURL:
    import.meta.env.VITE_REFERENCE_API,
  timeout: 15_000,
});

export const searchApi = axios.create({
  baseURL:
    import.meta.env.VITE_SEARCH_API,
  timeout: 30_000,
});

export const agentApi = axios.create({
  baseURL:
    import.meta.env.VITE_AGENT_API,
  timeout: 45_000,
});

export const marketApi = axios.create({
  baseURL:
    import.meta.env.VITE_MARKET_API,
  timeout: 15_000,
});

export const rfqApi = axios.create({
  baseURL:
    import.meta.env.VITE_RFQ_API,
  timeout: 30_000,
});
