import { useMemo, useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  createRfq,
  DEMO_ACCOUNT_ID,
  executeRfqQuote,
  fetchRfq,
} from "../../services/rfq";
import { useMarketStore } from "../../store/useMarketStore";
import type {
  DealerQuote,
  RfqSide,
} from "../../types/bond";

function bestQuote(
  side: RfqSide,
  quotes: DealerQuote[],
): DealerQuote | null {
  const active = quotes.filter(
    (quote) =>
      quote.quote_status === "ACTIVE",
  );

  if (active.length === 0) {
    return null;
  }

  return side === "BUY"
    ? active.reduce((best, current) =>
        current.price < best.price
          ? current
          : best,
      )
    : active.reduce((best, current) =>
        current.price > best.price
          ? current
          : best,
      );
}

export function RfqPanel() {
  const queryClient = useQueryClient();

  const selectedBondId = useMarketStore(
    (state) => state.selectedBondId,
  );

  const [side, setSide] =
    useState<RfqSide>("BUY");

  const [quantity, setQuantity] =
    useState(1_000_000);

  const [activeRfqId, setActiveRfqId] =
    useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: createRfq,
    onSuccess: (rfq) => {
      setActiveRfqId(rfq.id);
    },
  });

  const {
    data: detail,
    isError: rfqLoadFailed,
  } = useQuery({
    queryKey: ["rfq-detail", activeRfqId],
    queryFn: () =>
      fetchRfq(activeRfqId as string),
    enabled: activeRfqId !== null,
    refetchInterval: (query) => {
      const data = query.state.data;

      if (
        data?.rfq.status === "EXECUTED"
        || data?.rfq.status === "CANCELLED"
        || data?.rfq.status === "EXPIRED"
      ) {
        return false;
      }

      return 500;
    },
  });

  const activeQuotes =
    detail?.quotes.filter(
      (quote) =>
        quote.quote_status === "ACTIVE",
    ) ?? [];

  const selectedBestQuote = useMemo(
    () =>
      detail
        ? bestQuote(
            detail.rfq.side,
            detail.quotes,
          )
        : null,
    [detail],
  );

  const executeMutation = useMutation({
    mutationFn: ({
      rfqId,
      quoteId,
    }: {
      rfqId: string;
      quoteId: string;
    }) =>
      executeRfqQuote(
        rfqId,
        quoteId,
      ),

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            "rfq-detail",
            activeRfqId,
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            "live-account-risk",
          ],
        }),
      ]);
    },
  });

  function submitRfq() {
    if (selectedBondId === null) {
      return;
    }

    createMutation.mutate({
      account_id: DEMO_ACCOUNT_ID,
      instrument_id: selectedBondId,
      side,
      quantity,
      client: "Mercator Demo Fund",
    });
  }

  function executeBestQuote() {
    if (
      !detail
      || !selectedBestQuote
    ) {
      return;
    }

    executeMutation.mutate({
      rfqId: detail.rfq.id,
      quoteId: selectedBestQuote.id,
    });
  }

  return (
    <section className="rfq-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Electronic trading
          </span>
          <h2>Request for quote</h2>
        </div>

        <span>
          {selectedBondId !== null
            ? `Instrument #${selectedBondId}`
            : "No instrument selected"}
        </span>
      </div>

      <div className="rfq-form">
        <label>
          Side
          <select
            value={side}
            onChange={(event) =>
              setSide(
                event.target.value as RfqSide,
              )
            }
          >
            <option value="BUY">BUY</option>
            <option value="SELL">
              SELL
            </option>
          </select>
        </label>

        <label>
          Quantity
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(event) =>
              setQuantity(
                Number(event.target.value),
              )
            }
          />
        </label>
      </div>

      <button
        type="button"
        onClick={submitRfq}
        disabled={
          selectedBondId === null
          || quantity <= 0
          || createMutation.isPending
        }
      >
        {createMutation.isPending
          ? "Submitting RFQ..."
          : "Request dealer quotes"}
      </button>

      {createMutation.isError && (
        <p className="error-text">
          RFQ creation failed.
        </p>
      )}

      {rfqLoadFailed && (
        <p className="error-text">
          Could not load RFQ quotes.
        </p>
      )}

      {detail && (
        <div className="rfq-session">
          <div className="rfq-session-header">
            <div>
              <span>Status</span>
              <strong>
                {detail.rfq.status}
              </strong>
            </div>

            <div>
              <span>RFQ ID</span>
              <code>{detail.rfq.id}</code>
            </div>
          </div>

          <div className="dealer-quote-list">
            {detail.quotes.map((quote) => {
              const isBest =
                selectedBestQuote?.id
                === quote.id;

              return (
                <article
                  key={quote.id}
                  className={
                    isBest
                      ? "best-dealer-quote"
                      : ""
                  }
                >
                  <div>
                    <strong>
                      {quote.dealer}
                    </strong>

                    {isBest && (
                      <span className="best-badge">
                        BEST
                      </span>
                    )}
                  </div>

                  <div>
                    <span>Price</span>
                    <strong>
                      {quote.price.toFixed(4)}
                    </strong>
                  </div>

                  <div>
                    <span>Half spread</span>
                    <strong>
                      {quote.spread_bps.toFixed(
                        2,
                      )}
                      bp
                    </strong>
                  </div>

                  <div>
                    <span>Latency</span>
                    <strong>
                      {quote.latency_ms} ms
                    </strong>
                  </div>

                  <div>
                    <span>Status</span>
                    <strong>
                      {quote.quote_status}
                    </strong>
                  </div>
                </article>
              );
            })}
          </div>

          {activeQuotes.length === 0
            && detail.rfq.status !==
              "EXECUTED" && (
              <p className="muted-text">
                Waiting for dealer quotes...
              </p>
            )}

          {selectedBestQuote
            && detail.rfq.status !==
              "EXECUTED" && (
              <button
                type="button"
                onClick={executeBestQuote}
                disabled={
                  executeMutation.isPending
                }
              >
                {executeMutation.isPending
                  ? "Executing..."
                  : `Execute best quote at ${selectedBestQuote.price.toFixed(
                      4,
                    )}`}
              </button>
            )}

          {executeMutation.isError && (
            <p className="error-text">
              Execution failed. The quote
              may have expired or the RFQ
              may already be complete.
            </p>
          )}

          {detail.rfq.status ===
            "EXECUTED" && (
            <p className="execution-success">
              Trade executed. Portfolio risk
              has been refreshed.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
