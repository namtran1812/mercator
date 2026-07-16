import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { AgentPanel } from "../components/AgentPanel/AgentPanel";
import { BondGrid } from "../components/BondGrid/BondGrid";
import { MarketSummary } from "../components/MarketSummary/MarketSummary";
import { fetchLatestPrices } from "../services/market";
import { useMarketStore } from "../store/useMarketStore";

export function Dashboard() {
  const setBonds = useMarketStore(
    (state) => state.setBonds,
  );

  const selectedBondId = useMarketStore(
    (state) => state.selectedBondId,
  );

  const bonds = useMarketStore(
    (state) => state.bonds,
  );

  const {
    data,
    isLoading,
    isError,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ["latest-prices"],
    queryFn: () => fetchLatestPrices(250),
  });

  useEffect(() => {
    if (data) {
      setBonds(data);
    }
  }, [data, setBonds]);

  const selectedBond = bonds.find(
    (bond) =>
      bond.instrument_id === selectedBondId,
  );

  return (
    <main className="terminal-shell">
      <header className="terminal-header">
        <div>
          <span className="eyebrow">
            Fixed-Income Intelligence Platform
          </span>
          <h1>Mercator</h1>
        </div>

        <div className="header-status">
          <span>
            {isLoading
              ? "Loading prices"
              : `${bonds.length} instruments`}
          </span>

          <span>
            {dataUpdatedAt
              ? new Date(
                  dataUpdatedAt,
                ).toLocaleTimeString()
              : "Not updated"}
          </span>

          <span
            className={
              isError
                ? "error-indicator"
                : "live-indicator"
            }
          >
            {isError ? "DISCONNECTED" : "LIVE"}
          </span>
        </div>
      </header>

      <MarketSummary />

      <section className="workspace">
        <div className="market-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                Pricing universe
              </span>
              <h2>Corporate bonds</h2>
            </div>

            <span>
              {selectedBond
                ? `Selected #${selectedBond.instrument_id}`
                : "Select an instrument"}
            </span>
          </div>

          {isError && (
            <p className="error-text">
              Market API is unavailable on port
              8005.
            </p>
          )}

          <BondGrid />
        </div>

        <AgentPanel />
      </section>
    </main>
  );
}
