import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AgentPanel } from "../components/AgentPanel/AgentPanel";
import { BondGrid } from "../components/BondGrid/BondGrid";
import { BondDetails } from "../components/BondDetails/BondDetails";
import { MarketSummary } from "../components/MarketSummary/MarketSummary";
import { ScenarioPanel } from "../components/ScenarioPanel/ScenarioPanel";
import { PortfolioPanel } from "../components/PortfolioPanel/PortfolioPanel";
import { ReplayPanel } from "../components/ReplayPanel/ReplayPanel";
import { LivePnlPanel } from "../components/LivePnlPanel/LivePnlPanel";
import { RfqPanel } from "../components/RfqPanel/RfqPanel";
import { RfqAnalyticsPanel } from "../components/RfqAnalyticsPanel/RfqAnalyticsPanel";
import { RelativeValuePanel } from "../components/RelativeValuePanel/RelativeValuePanel";
import { CarryRollPanel } from "../components/CarryRollPanel/CarryRollPanel";

import { fetchLatestPrices } from "../services/market";
import { useMarketStore } from "../store/useMarketStore";
import { usePriceStream } from "../hooks/usePriceStream";

type WorkspaceTab =
  | "analysis"
  | "relative-value"
  | "provenance";

type AdvancedTab =
  | "scenario"
  | "carry"
  | "portfolio"
  | "pnl"
  | "rfq";

export function Dashboard() {
  usePriceStream();

  const [workspaceTab, setWorkspaceTab] =
    useState<WorkspaceTab>("analysis");

  const [advancedOpen, setAdvancedOpen] =
    useState(false);

  const [advancedTab, setAdvancedTab] =
    useState<AdvancedTab>("scenario");

  const setBonds = useMarketStore(
    (state) => state.setBonds,
  );

  const selectedBondId = useMarketStore(
    (state) => state.selectedBondId,
  );

  const bonds = useMarketStore(
    (state) => state.bonds,
  );

  const lastStreamUpdate = useMarketStore(
    (state) => state.lastStreamUpdate,
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
            Fixed-Income Intelligence
          </span>

          <h1>Mercator</h1>
        </div>

        <div className="header-status">
          <span>
            {isLoading
              ? "Loading"
              : `${bonds.length} instruments`}
          </span>

          {lastStreamUpdate && (
            <span className="desktop-status">
              {lastStreamUpdate.dependencyTenor}
              {" · "}
              {(
                lastStreamUpdate.dependencyWeight
                * 100
              ).toFixed(1)}
              %
            </span>
          )}

          <span
            className={
              isError
                ? "error-indicator"
                : "live-indicator"
            }
          >
            {isError ? "OFFLINE" : "LIVE"}
          </span>

          {dataUpdatedAt > 0 && (
            <span className="desktop-status">
              {new Date(
                dataUpdatedAt,
              ).toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      <MarketSummary />

      {isError && (
        <div className="system-alert">
          Market API unavailable.
        </div>
      )}

      <section className="primary-workspace">
        <section className="market-panel universe-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                Market
              </span>

              <h2>Corporate bonds</h2>
            </div>

            <span className="panel-meta">
              {selectedBond
                ? `#${selectedBond.instrument_id}`
                : "Select instrument"}
            </span>
          </div>

          <BondGrid />
        </section>

        <section className="security-workspace">
          <BondDetails />
        </section>
      </section>

      <section className="analysis-workspace">
        <div className="workspace-tabs">
          <button
            type="button"
            className={
              workspaceTab === "analysis"
                ? "workspace-tab active"
                : "workspace-tab"
            }
            onClick={() =>
              setWorkspaceTab("analysis")
            }
          >
            Analysis
          </button>

          <button
            type="button"
            className={
              workspaceTab === "relative-value"
                ? "workspace-tab active"
                : "workspace-tab"
            }
            onClick={() =>
              setWorkspaceTab(
                "relative-value",
              )
            }
          >
            Relative value
          </button>

          <button
            type="button"
            className={
              workspaceTab === "provenance"
                ? "workspace-tab active"
                : "workspace-tab"
            }
            onClick={() =>
              setWorkspaceTab("provenance")
            }
          >
            Replay
          </button>
        </div>

        <div className="workspace-content">
          {workspaceTab === "analysis" && (
            <AgentPanel />
          )}

          {workspaceTab === "relative-value" && (
            <RelativeValuePanel />
          )}

          {workspaceTab === "provenance" && (
            <ReplayPanel />
          )}
        </div>
      </section>

      <section className="advanced-workspace">
        <button
          type="button"
          className="advanced-toggle"
          onClick={() =>
            setAdvancedOpen(
              (current) => !current,
            )
          }
        >
          <span>
            <span className="eyebrow">
              Tools
            </span>

            <strong>
              Advanced analytics
            </strong>
          </span>

          <span>
            {advancedOpen ? "−" : "+"}
          </span>
        </button>

        {advancedOpen && (
          <div className="advanced-content">
            <nav className="advanced-tabs">
              <button
                type="button"
                className={
                  advancedTab === "scenario"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setAdvancedTab("scenario")
                }
              >
                Scenario
              </button>

              <button
                type="button"
                className={
                  advancedTab === "carry"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setAdvancedTab("carry")
                }
              >
                Carry & Roll
              </button>

              <button
                type="button"
                className={
                  advancedTab === "portfolio"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setAdvancedTab("portfolio")
                }
              >
                Portfolio
              </button>

              <button
                type="button"
                className={
                  advancedTab === "pnl"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setAdvancedTab("pnl")
                }
              >
                Live P&L
              </button>

              <button
                type="button"
                className={
                  advancedTab === "rfq"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setAdvancedTab("rfq")
                }
              >
                RFQ
              </button>
            </nav>

            <div className="advanced-panel">
              {advancedTab === "scenario" && (
                <ScenarioPanel />
              )}

              {advancedTab === "carry" && (
                <CarryRollPanel />
              )}

              {advancedTab === "portfolio" && (
                <PortfolioPanel />
              )}

              {advancedTab === "pnl" && (
                <LivePnlPanel />
              )}

              {advancedTab === "rfq" && (
                <>
                  <RfqPanel />
                  <RfqAnalyticsPanel />
                </>
              )}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
