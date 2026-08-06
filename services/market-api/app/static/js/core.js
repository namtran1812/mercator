const state = {
      socket: null,
      prices: new Map(),
      scenario: null,
      sequence: 0,
    };

    let currentPriceHistory = [];
    let currentMarketOverview = [];

    const elements = {
      instrumentIds: document.getElementById("instrumentIds"),
      positionNotional: document.getElementById("positionNotional"),
      treasuryShift: document.getElementById("treasuryShift"),
      spreadShift: document.getElementById("spreadShift"),
      liquidityHaircut: document.getElementById("liquidityHaircut"),
      downgradeNotches: document.getElementById("downgradeNotches"),
      connectionDot: document.getElementById("connectionDot"),
      connectionText: document.getElementById("connectionText"),
      marketValue: document.getElementById("marketValue"),
      scenarioPnl: document.getElementById("scenarioPnl"),
      treasuryPnl: document.getElementById("treasuryPnl"),
      spreadPnl: document.getElementById("spreadPnl"),
      streamSequence: document.getElementById("streamSequence"),
      instrumentCount: document.getElementById("instrumentCount"),
      instrumentRows: document.getElementById("instrumentRows"),
      attributeTreasury: document.getElementById("attributeTreasury"),
      attributeSpread: document.getElementById("attributeSpread"),
      attributeLiquidity: document.getElementById("attributeLiquidity"),
      attributeDowngrade: document.getElementById("attributeDowngrade"),
      attributeTotal: document.getElementById("attributeTotal"),
      eventLog: document.getElementById("eventLog"),
      startButton: document.getElementById("startButton"),
      stopButton: document.getElementById("stopButton"),
      scenarioButton: document.getElementById("scenarioButton"),
      exportButton: document.getElementById("exportButton"),

      optimizerNotional:
        document.getElementById("optimizerNotional"),
      optimizerMaxPosition:
        document.getElementById("optimizerMaxPosition"),
      optimizerObjective:
        document.getElementById("optimizerObjective"),
      runOptimizerButton:
        document.getElementById("runOptimizerButton"),
      optimizerResultObjective:
        document.getElementById("optimizerResultObjective"),
      optimizerResultNotional:
        document.getElementById("optimizerResultNotional"),
      optimizerAllocatedNotional:
        document.getElementById("optimizerAllocatedNotional"),
      optimizerAllocationCount:
        document.getElementById("optimizerAllocationCount"),
      optimizerRows:
        document.getElementById("optimizerRows"),

      riskOptimizerNotional:
        document.getElementById("riskOptimizerNotional"),
      riskOptimizerMaxPosition:
        document.getElementById("riskOptimizerMaxPosition"),
      riskOptimizerDv01:
        document.getElementById("riskOptimizerDv01"),
      riskOptimizerCs01:
        document.getElementById("riskOptimizerCs01"),
      riskOptimizerObjective:
        document.getElementById("riskOptimizerObjective"),
      runRiskOptimizerButton:
        document.getElementById("runRiskOptimizerButton"),
      riskOptimizerInvested:
        document.getElementById("riskOptimizerInvested"),
      riskOptimizerCash:
        document.getElementById("riskOptimizerCash"),
      riskOptimizerInvestedPercent:
        document.getElementById("riskOptimizerInvestedPercent"),
      riskOptimizerPortfolioDv01:
        document.getElementById("riskOptimizerPortfolioDv01"),
      riskOptimizerPortfolioCs01:
        document.getElementById("riskOptimizerPortfolioCs01"),
      riskOptimizerAllocationCount:
        document.getElementById("riskOptimizerAllocationCount"),
      riskOptimizerRows:
        document.getElementById("riskOptimizerRows"),

      historicalVarPositionNotional:
        document.getElementById(
          "historicalVarPositionNotional"
        ),
      historicalVarConfidence:
        document.getElementById(
          "historicalVarConfidence"
        ),
      historicalVarLookback:
        document.getElementById(
          "historicalVarLookback"
        ),
      historicalVarSeed:
        document.getElementById(
          "historicalVarSeed"
        ),
      runHistoricalVarButton:
        document.getElementById(
          "runHistoricalVarButton"
        ),
      historicalVarValue:
        document.getElementById(
          "historicalVarValue"
        ),
      historicalVarExpectedShortfall:
        document.getElementById(
          "historicalVarExpectedShortfall"
        ),
      historicalVarWorstLoss:
        document.getElementById(
          "historicalVarWorstLoss"
        ),
      historicalVarMarketValue:
        document.getElementById(
          "historicalVarMarketValue"
        ),
      historicalVarAveragePnl:
        document.getElementById(
          "historicalVarAveragePnl"
        ),
      historicalVarVolatility:
        document.getElementById(
          "historicalVarVolatility"
        ),
      historicalVarConfidenceResult:
        document.getElementById(
          "historicalVarConfidenceResult"
        ),
      historicalVarObservationCount:
        document.getElementById(
          "historicalVarObservationCount"
        ),
      historicalVarObservationRows:
        document.getElementById(
          "historicalVarObservationRows"
        ),
      historicalVarContributionRows:
        document.getElementById(
          "historicalVarContributionRows"
        ),

      hedgePositionNotional:
        document.getElementById(
          "hedgePositionNotional"
        ),
      hedgeRatio:
        document.getElementById(
          "hedgeRatio"
        ),
      includeCreditHedge:
        document.getElementById(
          "includeCreditHedge"
        ),
      runHedgeRecommendationsButton:
        document.getElementById(
          "runHedgeRecommendationsButton"
        ),
      hedgeMarketValue:
        document.getElementById(
          "hedgeMarketValue"
        ),
      hedgeTotalDv01:
        document.getElementById(
          "hedgeTotalDv01"
        ),
      hedgeTotalCs01:
        document.getElementById(
          "hedgeTotalCs01"
        ),
      hedgeRatioResult:
        document.getElementById(
          "hedgeRatioResult"
        ),
      hedgeResidualDv01:
        document.getElementById(
          "hedgeResidualDv01"
        ),
      hedgeResidualCs01:
        document.getElementById(
          "hedgeResidualCs01"
        ),
      hedgeDv01Reduction:
        document.getElementById(
          "hedgeDv01Reduction"
        ),
      hedgeCs01Reduction:
        document.getElementById(
          "hedgeCs01Reduction"
        ),
      treasuryHedgeRows:
        document.getElementById(
          "treasuryHedgeRows"
        ),
      creditHedgeResult:
        document.getElementById(
          "creditHedgeResult"
        ),

      relativeValueBucketWidth:
        document.getElementById(
          "relativeValueBucketWidth"
        ),
      relativeValueMinimumPeers:
        document.getElementById(
          "relativeValueMinimumPeers"
        ),
      runRelativeValueButton:
        document.getElementById(
          "runRelativeValueButton"
        ),
      relativeValueInstrumentCount:
        document.getElementById(
          "relativeValueInstrumentCount"
        ),
      relativeValueOpportunityCount:
        document.getElementById(
          "relativeValueOpportunityCount"
        ),
      relativeValueAverageSpread:
        document.getElementById(
          "relativeValueAverageSpread"
        ),
      relativeValueAverageDuration:
        document.getElementById(
          "relativeValueAverageDuration"
        ),
      relativeValueRows:
        document.getElementById(
          "relativeValueRows"
        ),

      priceHistoryInstrumentId:
        document.getElementById(
          "priceHistoryInstrumentId"
        ),
      priceHistoryLimit:
        document.getElementById(
          "priceHistoryLimit"
        ),
      priceHistoryMetric:
        document.getElementById(
          "priceHistoryMetric"
        ),
      runPriceHistoryButton:
        document.getElementById(
          "runPriceHistoryButton"
        ),
      priceHistoryObservationCount:
        document.getElementById(
          "priceHistoryObservationCount"
        ),
      priceHistoryLatestPrice:
        document.getElementById(
          "priceHistoryLatestPrice"
        ),
      priceHistoryLatestYield:
        document.getElementById(
          "priceHistoryLatestYield"
        ),
      priceHistoryLatestSpread:
        document.getElementById(
          "priceHistoryLatestSpread"
        ),
      priceHistoryLatestDuration:
        document.getElementById(
          "priceHistoryLatestDuration"
        ),
      priceHistoryLatestQuality:
        document.getElementById(
          "priceHistoryLatestQuality"
        ),
      priceHistoryCurveVersion:
        document.getElementById(
          "priceHistoryCurveVersion"
        ),
      priceHistoryModelVersion:
        document.getElementById(
          "priceHistoryModelVersion"
        ),
      priceHistoryChartTitle:
        document.getElementById(
          "priceHistoryChartTitle"
        ),
      priceHistoryChartRange:
        document.getElementById(
          "priceHistoryChartRange"
        ),
      priceHistoryChart:
        document.getElementById(
          "priceHistoryChart"
        ),
      priceHistoryRows:
        document.getElementById(
          "priceHistoryRows"
        ),

      riskDecompositionNotional:
        document.getElementById(
          "riskDecompositionNotional"
        ),
      runRiskDecompositionButton:
        document.getElementById(
          "runRiskDecompositionButton"
        ),
      riskDecompositionInstrumentCount:
        document.getElementById(
          "riskDecompositionInstrumentCount"
        ),
      riskDecompositionMarketValue:
        document.getElementById(
          "riskDecompositionMarketValue"
        ),
      riskDecompositionDv01:
        document.getElementById(
          "riskDecompositionDv01"
        ),
      riskDecompositionCs01:
        document.getElementById(
          "riskDecompositionCs01"
        ),
      riskDecompositionKeyRateRows:
        document.getElementById(
          "riskDecompositionKeyRateRows"
        ),
      riskDecompositionInstrumentRows:
        document.getElementById(
          "riskDecompositionInstrumentRows"
        ),

      carryRollHorizon:
        document.getElementById(
          "carryRollHorizon"
        ),
      carryRollFinancingRate:
        document.getElementById(
          "carryRollFinancingRate"
        ),
      carryRollNormalization:
        document.getElementById(
          "carryRollNormalization"
        ),
      runCarryRollButton:
        document.getElementById(
          "runCarryRollButton"
        ),
      carryRollInstrumentCount:
        document.getElementById(
          "carryRollInstrumentCount"
        ),
      carryRollHorizonResult:
        document.getElementById(
          "carryRollHorizonResult"
        ),
      carryRollAverageReturn:
        document.getElementById(
          "carryRollAverageReturn"
        ),
      carryRollTopOpportunity:
        document.getElementById(
          "carryRollTopOpportunity"
        ),
      carryRollRows:
        document.getElementById(
          "carryRollRows"
        ),

      stressPositionNotional:
        document.getElementById(
          "stressPositionNotional"
        ),
      stressTreasuryParallel:
        document.getElementById(
          "stressTreasuryParallel"
        ),
      stressTreasury2Y:
        document.getElementById(
          "stressTreasury2Y"
        ),
      stressTreasury5Y:
        document.getElementById(
          "stressTreasury5Y"
        ),
      stressTreasury10Y:
        document.getElementById(
          "stressTreasury10Y"
        ),
      stressTreasury30Y:
        document.getElementById(
          "stressTreasury30Y"
        ),
      stressCreditParallel:
        document.getElementById(
          "stressCreditParallel"
        ),
      runStressTestButton:
        document.getElementById(
          "runStressTestButton"
        ),
      stressInstrumentCount:
        document.getElementById(
          "stressInstrumentCount"
        ),
      stressMarketValue:
        document.getElementById(
          "stressMarketValue"
        ),
      stressTreasuryPnl:
        document.getElementById(
          "stressTreasuryPnl"
        ),
      stressCreditPnl:
        document.getElementById(
          "stressCreditPnl"
        ),
      stressTotalPnl:
        document.getElementById(
          "stressTotalPnl"
        ),
      stressTestRows:
        document.getElementById(
          "stressTestRows"
        ),

      portfolioRiskFaceValue:
        document.getElementById(
          "portfolioRiskFaceValue"
        ),
      runPortfolioRiskButton:
        document.getElementById(
          "runPortfolioRiskButton"
        ),
      portfolioRiskPositionCount:
        document.getElementById(
          "portfolioRiskPositionCount"
        ),
      portfolioRiskTotalFaceValue:
        document.getElementById(
          "portfolioRiskTotalFaceValue"
        ),
      portfolioRiskMarketValue:
        document.getElementById(
          "portfolioRiskMarketValue"
        ),
      portfolioRiskWeightedYield:
        document.getElementById(
          "portfolioRiskWeightedYield"
        ),
      portfolioRiskWeightedSpread:
        document.getElementById(
          "portfolioRiskWeightedSpread"
        ),
      portfolioRiskWeightedDuration:
        document.getElementById(
          "portfolioRiskWeightedDuration"
        ),
      portfolioRiskWeightedConvexity:
        document.getElementById(
          "portfolioRiskWeightedConvexity"
        ),
      portfolioRiskTotalDv01:
        document.getElementById(
          "portfolioRiskTotalDv01"
        ),
      portfolioRiskConvexityContribution:
        document.getElementById(
          "portfolioRiskConvexityContribution"
        ),
      portfolioRiskRows:
        document.getElementById(
          "portfolioRiskRows"
        ),

      marketOverviewLimit:
        document.getElementById(
          "marketOverviewLimit"
        ),
      marketOverviewQuality:
        document.getElementById(
          "marketOverviewQuality"
        ),
      marketOverviewSearch:
        document.getElementById(
          "marketOverviewSearch"
        ),
      loadMarketOverviewButton:
        document.getElementById(
          "loadMarketOverviewButton"
        ),
      marketSummaryInstrumentCount:
        document.getElementById(
          "marketSummaryInstrumentCount"
        ),
      marketSummaryAveragePrice:
        document.getElementById(
          "marketSummaryAveragePrice"
        ),
      marketSummaryAverageYield:
        document.getElementById(
          "marketSummaryAverageYield"
        ),
      marketSummaryAverageSpread:
        document.getElementById(
          "marketSummaryAverageSpread"
        ),
      marketSummaryWidestInstrument:
        document.getElementById(
          "marketSummaryWidestInstrument"
        ),
      marketSummaryWidestSpread:
        document.getElementById(
          "marketSummaryWidestSpread"
        ),
      marketOverviewVisibleCount:
        document.getElementById(
          "marketOverviewVisibleCount"
        ),
      marketOverviewRows:
        document.getElementById(
          "marketOverviewRows"
        ),

      streamIntervalMs:
        document.getElementById(
          "streamIntervalMs"
        ),
      streamVolatilityBps:
        document.getElementById(
          "streamVolatilityBps"
        ),
      startMarketStreamButton:
        document.getElementById(
          "startMarketStreamButton"
        ),
      stopMarketStreamButton:
        document.getElementById(
          "stopMarketStreamButton"
        ),
      refreshMarketStreamStatusButton:
        document.getElementById(
          "refreshMarketStreamStatusButton"
        ),
      streamStatusRunning:
        document.getElementById(
          "streamStatusRunning"
        ),
      streamStatusClients:
        document.getElementById(
          "streamStatusClients"
        ),
      streamStatusInstruments:
        document.getElementById(
          "streamStatusInstruments"
        ),
      streamStatusInterval:
        document.getElementById(
          "streamStatusInterval"
        ),
      streamStatusSequence:
        document.getElementById(
          "streamStatusSequence"
        ),
      loadReplayScenariosButton:
        document.getElementById(
          "loadReplayScenariosButton"
        ),
      replayScenarioRows:
        document.getElementById(
          "replayScenarioRows"
        ),
    };

    function parseInstrumentIds() {
      return elements.instrumentIds.value
        .split(",")
        .map((value) => Number(value.trim()))
        .filter((value) => Number.isInteger(value) && value > 0);
    }

    function currency(value) {
      return new Intl.NumberFormat(
        "en-US",
        {
          style: "currency",
          currency: "USD",
          maximumFractionDigits: 0,
        },
      ).format(Number(value || 0));
    }

    function number(value, digits = 4) {
      return Number(value || 0).toLocaleString(
        "en-US",
        {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        },
      );
    }

    function percent(value) {
      return `${(Number(value || 0) * 100).toFixed(3)}%`;
    }

    function setPnlClass(element, value) {
      element.classList.remove("positive", "negative");

      if (value > 0) {
        element.classList.add("positive");
      } else if (value < 0) {
        element.classList.add("negative");
      }
    }

    function log(message) {
      const timestamp = new Date().toLocaleTimeString();
      const line = `[${timestamp}] ${message}`;

      elements.eventLog.textContent =
        `${line}\n${elements.eventLog.textContent}`
          .slice(0, 10000);
    }

    function setConnection(status, message) {
      elements.connectionDot.className = `dot ${status}`;
      elements.connectionText.textContent = message;
    }

    function scenarioByInstrument() {
      const values = state.scenario?.instruments || [];

      return new Map(
        values.map((item) => [
          item.instrument_id,
          item,
        ]),
      );
    }

    function render() {
      const positionNotional =
        Number(elements.positionNotional.value || 0);

      const marketValue = Array.from(state.prices.values())
        .reduce(
          (total, price) =>
            total
            + positionNotional
            * Number(price.clean_price)
            / 100,
          0,
        );

      elements.marketValue.textContent = currency(marketValue);
      elements.streamSequence.textContent =
        state.sequence.toLocaleString();

      const scenario = state.scenario || {
        total_pnl: 0,
        treasury_pnl: 0,
        spread_pnl: 0,
        liquidity_pnl: 0,
        downgrade_pnl: 0,
        instruments: [],
      };

      elements.scenarioPnl.textContent =
        currency(scenario.total_pnl);

      elements.treasuryPnl.textContent =
        currency(scenario.treasury_pnl);

      elements.spreadPnl.textContent =
        currency(scenario.spread_pnl);

      elements.attributeTreasury.textContent =
        currency(scenario.treasury_pnl);

      elements.attributeSpread.textContent =
        currency(scenario.spread_pnl);

      elements.attributeLiquidity.textContent =
        currency(scenario.liquidity_pnl);

      elements.attributeDowngrade.textContent =
        currency(scenario.downgrade_pnl);

      elements.attributeTotal.textContent =
        currency(scenario.total_pnl);

      [
        [elements.scenarioPnl, scenario.total_pnl],
        [elements.treasuryPnl, scenario.treasury_pnl],
        [elements.spreadPnl, scenario.spread_pnl],
        [elements.attributeTreasury, scenario.treasury_pnl],
        [elements.attributeSpread, scenario.spread_pnl],
        [elements.attributeLiquidity, scenario.liquidity_pnl],
        [elements.attributeDowngrade, scenario.downgrade_pnl],
        [elements.attributeTotal, scenario.total_pnl],
      ].forEach(([element, value]) => {
        setPnlClass(element, value);
      });

      const prices = Array.from(state.prices.values())
        .sort(
          (first, second) =>
            first.instrument_id - second.instrument_id,
        );

      elements.instrumentCount.textContent =
        `${prices.length} instrument${prices.length === 1 ? "" : "s"}`;

      if (prices.length === 0) {
        elements.instrumentRows.innerHTML = `
          <tr>
            <td colspan="8" class="empty">
              Start the market stream to receive prices.
            </td>
          </tr>
        `;
        return;
      }

      const scenarioMap = scenarioByInstrument();

      elements.instrumentRows.innerHTML = prices
        .map((price) => {
          const result = scenarioMap.get(
            price.instrument_id,
          );

          const pnl = Number(result?.pnl || 0);
          const change = Number(price.price_change || 0);

          return `
            <tr>
              <td>#${price.instrument_id}</td>
              <td>${number(price.clean_price, 4)}</td>
              <td class="${change >= 0 ? "positive" : "negative"}">
                ${change >= 0 ? "+" : ""}${number(change, 5)}
              </td>
              <td>${percent(price.yield_to_maturity)}</td>
              <td>${number(price.g_spread_bps, 2)} bp</td>
              <td>${number(price.modified_duration, 3)}</td>
              <td>
                ${currency(
                  positionNotional
                  * Number(price.clean_price)
                  / 100,
                )}
              </td>
              <td class="${pnl >= 0 ? "positive" : "negative"}">
                ${currency(pnl)}
              </td>
            </tr>
          `;
        })
        .join("");
    }

    async function request(path, options = {}) {
      const response = await fetch(path, options);

      const text = await response.text();

      let payload;

      try {
        payload = text ? JSON.parse(text) : {};
      } catch {
        payload = { detail: text };
      }

      if (!response.ok) {
        throw new Error(
          payload.detail
          || `Request failed with HTTP ${response.status}`,
        );
      }

      return payload;
    }

    async function stopStreamSilently() {
      try {
        await request(
          "/stream/stop",
          {
            method: "POST",
          },
        );
      } catch {
        // The stream may already be stopped.
      }
    }

    function connectWebSocket() {
      if (state.socket) {
        state.socket.close();
      }

      const scheme =
        window.location.protocol === "https:"
          ? "wss"
          : "ws";

      const socketUrl =
        `${scheme}://${window.location.host}/ws/market-data`;

      const socket = new WebSocket(socketUrl);
      state.socket = socket;

      setConnection("", "Connecting");

      socket.addEventListener(
        "open",
        () => {
          setConnection("connected", "Live");
          log("WebSocket connected");
        },
      );

      socket.addEventListener(
        "message",
        (event) => {
          const payload = JSON.parse(event.data);

          if (payload.type === "connected") {
            log(payload.message);
            return;
          }

          if (payload.type !== "market_data") {
            return;
          }

          state.sequence = payload.sequence;

          for (const update of payload.updates) {
            state.prices.set(
              update.instrument_id,
              update,
            );
          }

          render();
        },
      );

      socket.addEventListener(
        "close",
        () => {
          setConnection("", "Disconnected");
          log("WebSocket disconnected");
        },
      );

      socket.addEventListener(
        "error",
        () => {
          setConnection("error", "Connection error");
          log("WebSocket connection error");
        },
      );
    }

    async function startStream() {
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length === 0) {
        throw new Error("Enter at least one instrument ID.");
      }

      await stopStreamSilently();

      connectWebSocket();

      await new Promise(
        (resolve) => setTimeout(resolve, 250),
      );

      const status = await request(
        "/stream/start",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            instrument_ids: instrumentIds,
            interval_ms: 500,
            volatility_bps: 2,
          }),
        },
      );

      log(
        `Stream started for ${status.instrument_count} instruments`,
      );
    }

    async function stopStream() {
      const status = await request(
        "/stream/stop",
        {
          method: "POST",
        },
      );

      if (state.socket) {
        state.socket.close();
        state.socket = null;
      }

      setConnection("", "Stopped");
      log(`Stream stopped; running=${status.running}`);
    }


// ============================================================
// Result freshness
// ============================================================

const resultFreshnessState = {};

let resultFreshnessLastStreamSequence = null;

function formatFreshnessTime(value) {
  if (!value) {
    return "Not calculated";
  }

  return new Date(
    value,
  ).toLocaleTimeString();
}

function renderResultFreshness(key) {
  const element =
    document.querySelector(
      `[data-result-key="${key}"]`,
    );

  if (!element) {
    return;
  }

  const state =
    resultFreshnessState[key];

  const text =
    element.querySelector(
      ".result-freshness-text",
    );

  element.classList.remove(
    "fresh",
    "stale",
    "error",
  );

  if (!state) {
    if (text) {
      text.textContent =
        "Not calculated";
    }

    return;
  }

  if (state.error) {
    element.classList.add(
      "error",
    );

    if (text) {
      text.textContent =
        "Calculation failed";
    }

    return;
  }

  if (state.stale) {
    element.classList.add(
      "stale",
    );

    if (text) {
      text.textContent =
        `Stale · ${formatFreshnessTime(
          state.calculatedAt,
        )}`;
    }

    return;
  }

  element.classList.add(
    "fresh",
  );

  if (text) {
    text.textContent =
      `Updated ${formatFreshnessTime(
        state.calculatedAt,
      )}`;
  }
}

function markResultFresh(key) {
  resultFreshnessState[key] = {
    calculatedAt:
      new Date().toISOString(),

    stale: false,
    error: false,
  };

  renderResultFreshness(key);
}

function markResultError(key) {
  resultFreshnessState[key] = {
    calculatedAt:
      new Date().toISOString(),

    stale: false,
    error: true,
  };

  renderResultFreshness(key);
}

function markAllResultsStale() {
  for (
    const [
      key,
      state,
    ]
    of Object.entries(
      resultFreshnessState,
    )
  ) {
    if (
      !state
      || state.error
      || state.stale
    ) {
      continue;
    }

    state.stale = true;

    renderResultFreshness(key);
  }
}

function updateFreshnessFromStreamStatus(
  streamStatus,
) {
  const sequence =
    Number(
      streamStatus?.sequence ?? 0,
    );

  if (
    resultFreshnessLastStreamSequence
      === null
  ) {
    resultFreshnessLastStreamSequence =
      sequence;

    return;
  }

  if (
    sequence
      > resultFreshnessLastStreamSequence
  ) {
    markAllResultsStale();
  }

  resultFreshnessLastStreamSequence =
    sequence;
}


// ============================================================
// Toast notifications
// ============================================================

function showToast(
  message,
  options = {},
) {
  const container =
    document.getElementById(
      "toastContainer",
    );

  if (!container) {
    return;
  }

  const {
    type = "info",
    title = (
      type === "success"
        ? "Success"
        : type === "error"
          ? "Error"
          : type === "warning"
            ? "Warning"
            : "Mercator"
    ),
    duration = 4500,
  } = options;

  const toast =
    document.createElement(
      "div",
    );

  toast.className =
    `toast ${type}`;

  toast.innerHTML = `
    <span
      class="toast-indicator"
    ></span>

    <div class="toast-content">
      <strong
        class="toast-title"
      ></strong>

      <span
        class="toast-message"
      ></span>
    </div>

    <button
      type="button"
      class="toast-close"
      aria-label="Dismiss notification"
    >
      ×
    </button>
  `;

  toast.querySelector(
    ".toast-title",
  ).textContent =
    String(title);

  toast.querySelector(
    ".toast-message",
  ).textContent =
    String(message);

  const remove = () => {
    toast.classList.remove(
      "visible",
    );

    window.setTimeout(
      () => toast.remove(),
      160,
    );
  };

  toast
    .querySelector(
      ".toast-close",
    )
    .addEventListener(
      "click",
      remove,
    );

  container.prepend(
    toast,
  );

  window.requestAnimationFrame(
    () => {
      toast.classList.add(
        "visible",
      );
    },
  );

  if (
    Number.isFinite(duration)
    && duration > 0
  ) {
    window.setTimeout(
      remove,
      duration,
    );
  }

  return toast;
}

function toastSuccess(
  message,
  title = "Success",
) {
  return showToast(
    message,
    {
      type: "success",
      title,
    },
  );
}

function toastError(
  message,
  title = "Error",
) {
  return showToast(
    message,
    {
      type: "error",
      title,
      duration: 6500,
    },
  );
}

function toastWarning(
  message,
  title = "Warning",
) {
  return showToast(
    message,
    {
      type: "warning",
      title,
    },
  );
}

function toastInfo(
  message,
  title = "Mercator",
) {
  return showToast(
    message,
    {
      type: "info",
      title,
    },
  );
}
