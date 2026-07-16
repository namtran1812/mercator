import { useMarketStore } from "../../store/useMarketStore";

export function MarketSummary() {
  const bonds = useMarketStore((state) => state.bonds);

  const averageSpread =
    bonds.length > 0
      ? bonds.reduce(
          (total, bond) => total + bond.g_spread_bps,
          0,
        ) / bonds.length
      : 0;

  const averageYield =
    bonds.length > 0
      ? bonds.reduce(
          (total, bond) => total + bond.yield_to_maturity,
          0,
        ) / bonds.length
      : 0;

  const widestBond =
    bonds.length > 0
      ? [...bonds].sort(
          (left, right) =>
            right.g_spread_bps - left.g_spread_bps,
        )[0]
      : null;

  return (
    <section className="summary-grid">
      <article className="metric-card">
        <span>Universe</span>
        <strong>{bonds.length}</strong>
        <small>selected bonds</small>
      </article>

      <article className="metric-card">
        <span>Average spread</span>
        <strong>{averageSpread.toFixed(1)} bp</strong>
        <small>G-spread</small>
      </article>

      <article className="metric-card">
        <span>Average yield</span>
        <strong>{(averageYield * 100).toFixed(2)}%</strong>
        <small>yield to maturity</small>
      </article>

      <article className="metric-card">
        <span>Widest instrument</span>
        <strong>
          {widestBond
            ? `#${widestBond.instrument_id}`
            : "—"}
        </strong>
        <small>
          {widestBond
            ? `${widestBond.g_spread_bps.toFixed(1)} bp`
            : "no data"}
        </small>
      </article>
    </section>
  );
}
