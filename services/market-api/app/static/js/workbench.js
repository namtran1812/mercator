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

    async function runScenario() {
      const payload = await request(
        "/risk/scenario-analysis",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            instrument_ids: parseInstrumentIds(),
            position_notional:
              Number(elements.positionNotional.value),
            treasury_shift_bps:
              Number(elements.treasuryShift.value),
            spread_shift_bps:
              Number(elements.spreadShift.value),
            liquidity_haircut_percent:
              Number(elements.liquidityHaircut.value),
            downgrade_notches:
              Number(elements.downgradeNotches.value),
          }),
        },
      );

      state.scenario = payload;
      render();

      log(
        `Scenario completed: total P&L ${currency(
          payload.total_pnl,
        )}`,
      );
    }


    function renderOptimizerResult(payload) {
      const allocations = payload.allocations || [];

      const allocatedNotional = allocations.reduce(
        (total, allocation) =>
          total + Number(allocation.target_notional || 0),
        0,
      );

      elements.optimizerResultObjective.textContent =
        String(payload.objective || "—")
          .replaceAll("_", " ");

      elements.optimizerResultNotional.textContent =
        currency(payload.total_notional);

      elements.optimizerAllocatedNotional.textContent =
        currency(allocatedNotional);

      elements.optimizerAllocationCount.textContent =
        allocations.length.toLocaleString();

      if (allocations.length === 0) {
        elements.optimizerRows.innerHTML = `
          <tr>
            <td colspan="4" class="empty">
              The optimizer returned no allocations.
            </td>
          </tr>
        `;

        return;
      }

      elements.optimizerRows.innerHTML = allocations
        .map((allocation) => `
          <tr>
            <td>#${allocation.instrument_id}</td>
            <td>
              ${(Number(allocation.weight || 0) * 100)
                .toFixed(2)}%
            </td>
            <td>
              ${currency(allocation.target_notional)}
            </td>
            <td>
              ${number(allocation.expected_score, 6)}
            </td>
          </tr>
        `)
        .join("");
    }

    async function runStandardOptimizer() {
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length < 2) {
        throw new Error(
          "The optimizer requires at least two instrument IDs.",
        );
      }

      const totalNotional = Number(
        elements.optimizerNotional.value,
      );

      const maxPositionPercent = Number(
        elements.optimizerMaxPosition.value,
      ) / 100;

      if (
        !Number.isFinite(totalNotional)
        || totalNotional <= 0
      ) {
        throw new Error(
          "Total notional must be greater than zero.",
        );
      }

      if (
        !Number.isFinite(maxPositionPercent)
        || maxPositionPercent <= 0
        || maxPositionPercent > 1
      ) {
        throw new Error(
          "Maximum position must be between 0 and 100 percent.",
        );
      }

      elements.runOptimizerButton.disabled = true;
      elements.runOptimizerButton.textContent =
        "Optimizing...";

      try {
        const payload = await request(
          "/portfolio/optimize",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              instrument_ids: instrumentIds,
              total_notional: totalNotional,
              max_position_percent: maxPositionPercent,
              objective:
                elements.optimizerObjective.value,
            }),
          },
        );

        renderOptimizerResult(payload);

        log(
          `Optimization completed: `
          + `${payload.allocations.length} allocations, `
          + `${currency(payload.total_notional)} total notional`,
        );
      } finally {
        elements.runOptimizerButton.disabled = false;
        elements.runOptimizerButton.textContent =
          "Run Optimization";
      }
    }


    function renderRiskOptimizerResult(payload) {
      const allocations = payload.allocations || [];

      elements.riskOptimizerInvested.textContent =
        currency(payload.invested_notional);

      elements.riskOptimizerCash.textContent =
        currency(payload.cash_notional);

      elements.riskOptimizerInvestedPercent.textContent =
        `${(Number(payload.invested_percent || 0) * 100)
          .toFixed(2)}%`;

      elements.riskOptimizerPortfolioDv01.textContent =
        number(payload.portfolio_dv01, 2);

      elements.riskOptimizerPortfolioCs01.textContent =
        number(payload.portfolio_cs01, 2);

      elements.riskOptimizerAllocationCount.textContent =
        allocations.length.toLocaleString();

      if (allocations.length === 0) {
        elements.riskOptimizerRows.innerHTML = `
          <tr>
            <td colspan="6" class="empty">
              The risk optimizer returned no allocations.
            </td>
          </tr>
        `;

        return;
      }

      elements.riskOptimizerRows.innerHTML = allocations
        .map((allocation) => `
          <tr>
            <td>#${allocation.instrument_id}</td>
            <td>
              ${(Number(allocation.weight || 0) * 100)
                .toFixed(2)}%
            </td>
            <td>
              ${currency(allocation.target_notional)}
            </td>
            <td>
              ${number(allocation.expected_score, 6)}
            </td>
            <td>
              ${number(allocation.dv01, 2)}
            </td>
            <td>
              ${number(allocation.cs01, 2)}
            </td>
          </tr>
        `)
        .join("");
    }

    async function runRiskBudgetOptimizer() {
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length < 2) {
        throw new Error(
          "The risk optimizer requires at least two instrument IDs.",
        );
      }

      const totalNotional = Number(
        elements.riskOptimizerNotional.value,
      );

      const maxPositionPercent = Number(
        elements.riskOptimizerMaxPosition.value,
      ) / 100;

      const maxPortfolioDv01 = Number(
        elements.riskOptimizerDv01.value,
      );

      const maxPortfolioCs01 = Number(
        elements.riskOptimizerCs01.value,
      );

      if (
        !Number.isFinite(totalNotional)
        || totalNotional <= 0
      ) {
        throw new Error(
          "Total notional must be greater than zero.",
        );
      }

      if (
        !Number.isFinite(maxPositionPercent)
        || maxPositionPercent <= 0
        || maxPositionPercent > 1
      ) {
        throw new Error(
          "Maximum position must be between 0 and 100 percent.",
        );
      }

      if (
        !Number.isFinite(maxPortfolioDv01)
        || maxPortfolioDv01 <= 0
      ) {
        throw new Error(
          "Maximum portfolio DV01 must be greater than zero.",
        );
      }

      if (
        !Number.isFinite(maxPortfolioCs01)
        || maxPortfolioCs01 <= 0
      ) {
        throw new Error(
          "Maximum portfolio CS01 must be greater than zero.",
        );
      }

      elements.runRiskOptimizerButton.disabled = true;
      elements.runRiskOptimizerButton.textContent =
        "Optimizing...";

      try {
        const payload = await request(
          "/portfolio/optimize-risk",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              instrument_ids: instrumentIds,
              total_notional: totalNotional,
              max_position_percent: maxPositionPercent,
              max_portfolio_dv01: maxPortfolioDv01,
              max_portfolio_cs01: maxPortfolioCs01,
              objective:
                elements.riskOptimizerObjective.value,
            }),
          },
        );

        renderRiskOptimizerResult(payload);

        log(
          `Risk optimization completed: `
          + `${allocationsDescription(payload)}, `
          + `DV01 ${number(payload.portfolio_dv01, 2)}, `
          + `CS01 ${number(payload.portfolio_cs01, 2)}`,
        );
      } finally {
        elements.runRiskOptimizerButton.disabled = false;
        elements.runRiskOptimizerButton.textContent =
          "Run Risk Optimization";
      }
    }

    function allocationsDescription(payload) {
      const count = (payload.allocations || []).length;

      return `${count} allocation${count === 1 ? "" : "s"}, `
        + `${currency(payload.invested_notional)} invested`;
    }


    function signedBps(value) {
      const numericValue = Number(value || 0);
      const sign = numericValue > 0 ? "+" : "";

      return `${sign}${numericValue.toFixed(2)} bps`;
    }

    function signedCurrency(value) {
      const numericValue = Number(value || 0);
      const sign = numericValue > 0 ? "+" : "";

      return `${sign}${currency(numericValue)}`;
    }

    function renderHistoricalVarResult(payload) {
      const observations = payload.observations || [];
      const contributions =
        payload.instrument_contributions || [];

      elements.historicalVarValue.textContent =
        currency(payload.value_at_risk);

      elements.historicalVarExpectedShortfall.textContent =
        currency(payload.expected_shortfall);

      elements.historicalVarWorstLoss.textContent =
        currency(payload.worst_historical_loss);

      elements.historicalVarMarketValue.textContent =
        currency(payload.total_market_value);

      elements.historicalVarAveragePnl.textContent =
        signedCurrency(payload.average_daily_pnl);

      elements.historicalVarVolatility.textContent =
        currency(payload.pnl_volatility);

      elements.historicalVarConfidenceResult.textContent =
        `${(
          Number(payload.confidence_level || 0) * 100
        ).toFixed(2)}%`;

      elements.historicalVarObservationCount.textContent =
        Number(
          payload.observation_count || observations.length
        ).toLocaleString();

      const worstObservations = [...observations]
        .sort(
          (left, right) =>
            Number(left.portfolio_pnl)
            - Number(right.portfolio_pnl),
        )
        .slice(0, 20);

      if (worstObservations.length === 0) {
        elements.historicalVarObservationRows.innerHTML = `
          <tr>
            <td colspan="4" class="empty">
              No historical observations were returned.
            </td>
          </tr>
        `;
      } else {
        elements.historicalVarObservationRows.innerHTML =
          worstObservations
            .map((observation) => `
              <tr>
                <td>
                  #${observation.observation_index}
                </td>
                <td>
                  ${signedBps(
                    observation.treasury_shock_bps
                  )}
                </td>
                <td>
                  ${signedBps(
                    observation.credit_shock_bps
                  )}
                </td>
                <td>
                  ${signedCurrency(
                    observation.portfolio_pnl
                  )}
                </td>
              </tr>
            `)
            .join("");
      }

      const sortedContributions = [...contributions]
        .sort(
          (left, right) =>
            Math.abs(Number(right.var_contribution || 0))
            - Math.abs(Number(left.var_contribution || 0)),
        );

      if (sortedContributions.length === 0) {
        elements.historicalVarContributionRows.innerHTML = `
          <tr>
            <td colspan="5" class="empty">
              No instrument contributions were returned.
            </td>
          </tr>
        `;
      } else {
        elements.historicalVarContributionRows.innerHTML =
          sortedContributions
            .map((contribution) => `
              <tr>
                <td>
                  #${contribution.instrument_id}
                </td>
                <td>
                  ${currency(contribution.market_value)}
                </td>
                <td>
                  ${number(contribution.dv01, 2)}
                </td>
                <td>
                  ${number(contribution.cs01, 2)}
                </td>
                <td>
                  ${currency(
                    contribution.var_contribution
                  )}
                </td>
              </tr>
            `)
            .join("");
      }
    }

    async function runHistoricalVar() {
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length < 1) {
        throw new Error(
          "Historical VaR requires at least one instrument ID.",
        );
      }

      const positionNotional = Number(
        elements.historicalVarPositionNotional.value,
      );

      const confidenceLevel = Number(
        elements.historicalVarConfidence.value,
      );

      const lookbackDays = Number(
        elements.historicalVarLookback.value,
      );

      const seed = Number(
        elements.historicalVarSeed.value,
      );

      if (
        !Number.isFinite(positionNotional)
        || positionNotional <= 0
        || positionNotional > 1000000000
      ) {
        throw new Error(
          "Position notional must be between 0 and $1 billion.",
        );
      }

      if (
        !Number.isFinite(confidenceLevel)
        || confidenceLevel < 0.9
        || confidenceLevel > 0.999
      ) {
        throw new Error(
          "Confidence level must be between 90% and 99.9%.",
        );
      }

      if (
        !Number.isInteger(lookbackDays)
        || lookbackDays < 30
        || lookbackDays > 5000
      ) {
        throw new Error(
          "Lookback days must be an integer between 30 and 5000.",
        );
      }

      if (
        !Number.isInteger(seed)
        || seed < 0
        || seed > 2147483647
      ) {
        throw new Error(
          "Seed must be an integer between 0 and 2147483647.",
        );
      }

      elements.runHistoricalVarButton.disabled = true;
      elements.runHistoricalVarButton.textContent =
        "Calculating...";

      try {
        const payload = await request(
          "/risk/historical-var",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              instrument_ids: instrumentIds,
              position_notional: positionNotional,
              confidence_level: confidenceLevel,
              lookback_days: lookbackDays,
              seed,
            }),
          },
        );

        renderHistoricalVarResult(payload);

        log(
          `Historical VaR completed: `
          + `${payload.instrument_count} instruments, `
          + `${payload.observation_count} observations, `
          + `VaR ${currency(payload.value_at_risk)}, `
          + `ES ${currency(payload.expected_shortfall)}`,
        );
      } finally {
        elements.runHistoricalVarButton.disabled = false;
        elements.runHistoricalVarButton.textContent =
          "Run Historical VaR";
      }
    }


    function riskReductionPercent(original, residual) {
      const originalValue =
        Math.abs(Number(original || 0));

      const residualValue =
        Math.abs(Number(residual || 0));

      if (originalValue === 0) {
        return residualValue === 0 ? 100 : 0;
      }

      const reduction =
        (1 - residualValue / originalValue) * 100;

      return Math.max(
        0,
        Math.min(100, reduction),
      );
    }

    function renderHedgeRecommendations(payload) {
      const treasuryHedges =
        payload.treasury_hedges || [];

      const dv01Reduction = riskReductionPercent(
        payload.total_dv01,
        payload.residual_dv01,
      );

      const cs01Reduction = riskReductionPercent(
        payload.total_cs01,
        payload.residual_cs01,
      );

      elements.hedgeMarketValue.textContent =
        currency(payload.total_market_value);

      elements.hedgeTotalDv01.textContent =
        number(payload.total_dv01, 2);

      elements.hedgeTotalCs01.textContent =
        number(payload.total_cs01, 2);

      elements.hedgeRatioResult.textContent =
        `${(
          Number(payload.hedge_ratio || 0) * 100
        ).toFixed(2)}%`;

      elements.hedgeResidualDv01.textContent =
        number(payload.residual_dv01, 2);

      elements.hedgeResidualCs01.textContent =
        number(payload.residual_cs01, 2);

      elements.hedgeDv01Reduction.textContent =
        `${dv01Reduction.toFixed(2)}%`;

      elements.hedgeCs01Reduction.textContent =
        `${cs01Reduction.toFixed(2)}%`;

      if (treasuryHedges.length === 0) {
        elements.treasuryHedgeRows.innerHTML = `
          <tr>
            <td colspan="5" class="empty">
              No Treasury hedges were recommended.
            </td>
          </tr>
        `;
      } else {
        const sortedHedges = [...treasuryHedges].sort(
          (left, right) =>
            Number(left.tenor_years || 0)
            - Number(right.tenor_years || 0),
        );

        elements.treasuryHedgeRows.innerHTML =
          sortedHedges
            .map((hedge) => `
              <tr>
                <td>${hedge.tenor}</td>

                <td>
                  ${number(hedge.tenor_years, 2)}
                </td>

                <td>
                  ${number(
                    hedge.portfolio_key_rate_dv01,
                    2,
                  )}
                </td>

                <td>
                  ${number(
                    hedge.hedge_instrument_dv01_per_million,
                    2,
                  )}
                </td>

                <td>
                  ${signedCurrency(
                    hedge.recommended_notional,
                  )}
                </td>
              </tr>
            `)
            .join("");
      }

      const creditHedge = payload.credit_hedge;

      if (!creditHedge) {
        elements.creditHedgeResult.className =
          "credit-hedge-empty";

        elements.creditHedgeResult.textContent =
          "Credit hedge was disabled or not required.";

        return;
      }

      elements.creditHedgeResult.className =
        "credit-hedge-card";

      elements.creditHedgeResult.innerHTML = `
        <div class="credit-hedge-instrument">
          ${creditHedge.hedge_instrument}
        </div>

        <div class="credit-hedge-metrics">
          <div class="credit-hedge-metric">
            <span>Portfolio CS01</span>

            <strong>
              ${number(
                creditHedge.portfolio_cs01,
                2,
              )}
            </strong>
          </div>

          <div class="credit-hedge-metric">
            <span>CS01 per $1MM</span>

            <strong>
              ${number(
                creditHedge.hedge_cs01_per_million,
                2,
              )}
            </strong>
          </div>

          <div class="credit-hedge-metric">
            <span>Recommended Notional</span>

            <strong>
              ${signedCurrency(
                creditHedge.recommended_notional,
              )}
            </strong>
          </div>
        </div>
      `;
    }

    async function runHedgeRecommendations() {
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length < 1) {
        throw new Error(
          "Hedge recommendations require at least one instrument ID.",
        );
      }

      const positionNotional = Number(
        elements.hedgePositionNotional.value,
      );

      const hedgeRatio = Number(
        elements.hedgeRatio.value,
      );

      if (
        !Number.isFinite(positionNotional)
        || positionNotional <= 0
        || positionNotional > 1000000000
      ) {
        throw new Error(
          "Position notional must be greater than zero and no more than $1 billion.",
        );
      }

      if (
        !Number.isFinite(hedgeRatio)
        || hedgeRatio < 0
        || hedgeRatio > 1.5
      ) {
        throw new Error(
          "Hedge ratio must be between 0 and 1.5.",
        );
      }

      elements.runHedgeRecommendationsButton.disabled =
        true;

      elements.runHedgeRecommendationsButton.textContent =
        "Generating...";

      try {
        const payload = await request(
          "/risk/hedge-recommendations",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              instrument_ids: instrumentIds,
              position_notional: positionNotional,
              hedge_ratio: hedgeRatio,
              include_credit_hedge:
                elements.includeCreditHedge.checked,
            }),
          },
        );

        renderHedgeRecommendations(payload);

        log(
          `Hedge recommendations completed: `
          + `${payload.instrument_count} instruments, `
          + `${(payload.treasury_hedges || []).length} `
          + `Treasury hedges, residual DV01 `
          + `${number(payload.residual_dv01, 2)}, `
          + `residual CS01 `
          + `${number(payload.residual_cs01, 2)}`,
        );
      } finally {
        elements.runHedgeRecommendationsButton.disabled =
          false;

        elements.runHedgeRecommendationsButton.textContent =
          "Generate Hedges";
      }
    }


    function relativeValueClassificationClass(value) {
      const classification = String(value || "")
        .trim()
        .toLowerCase();

      if (classification.includes("cheap")) {
        return "cheap";
      }

      if (classification.includes("rich")) {
        return "rich";
      }

      return "fair";
    }

    function signedNumber(value, digits = 2) {
      const numericValue = Number(value || 0);
      const sign = numericValue > 0 ? "+" : "";

      return `${sign}${number(numericValue, digits)}`;
    }

    function renderRelativeValueResult(payload) {
      const opportunities = payload.opportunities || [];

      elements.relativeValueInstrumentCount.textContent =
        Number(payload.instrument_count || 0)
          .toLocaleString();

      elements.relativeValueOpportunityCount.textContent =
        Number(payload.opportunity_count || opportunities.length)
          .toLocaleString();

      elements.relativeValueAverageSpread.textContent =
        `${number(payload.average_spread_bps, 2)} bp`;

      elements.relativeValueAverageDuration.textContent =
        number(payload.average_duration, 3);

      if (opportunities.length === 0) {
        elements.relativeValueRows.innerHTML = `
          <tr>
            <td colspan="11" class="empty">
              No relative-value opportunities were returned.
            </td>
          </tr>
        `;

        return;
      }

      const sortedOpportunities = [...opportunities].sort(
        (left, right) =>
          Number(right.conviction_score || 0)
          - Number(left.conviction_score || 0),
      );

      elements.relativeValueRows.innerHTML =
        sortedOpportunities
          .map((opportunity) => {
            const classification =
              String(opportunity.classification || "Fair");

            const classificationClass =
              relativeValueClassificationClass(
                classification,
              );

            const spreadDifference =
              Number(opportunity.spread_difference_bps || 0);

            const zScore =
              Number(opportunity.spread_z_score || 0);

            const spreadClass =
              spreadDifference > 0
                ? "relative-value-positive"
                : spreadDifference < 0
                  ? "relative-value-negative"
                  : "";

            const zScoreClass =
              zScore > 0
                ? "relative-value-positive"
                : zScore < 0
                  ? "relative-value-negative"
                  : "";

            return `
              <tr>
                <td>#${opportunity.instrument_id}</td>

                <td>
                  ${number(opportunity.clean_price, 4)}
                </td>

                <td>
                  ${percent(opportunity.yield_to_maturity)}
                </td>

                <td>
                  ${number(opportunity.g_spread_bps, 2)} bp
                </td>

                <td>
                  ${number(opportunity.modified_duration, 3)}
                </td>

                <td>
                  ${Number(opportunity.peer_count || 0)
                    .toLocaleString()}
                </td>

                <td>
                  ${number(
                    opportunity.peer_average_spread_bps,
                    2,
                  )} bp
                </td>

                <td class="${spreadClass}">
                  ${signedNumber(
                    opportunity.spread_difference_bps,
                    2,
                  )} bp
                </td>

                <td class="${zScoreClass}">
                  ${signedNumber(
                    opportunity.spread_z_score,
                    3,
                  )}
                </td>

                <td>
                  <span
                    class="
                      relative-value-classification
                      ${classificationClass}
                    "
                  >
                    ${classification}
                  </span>
                </td>

                <td class="relative-value-conviction">
                  ${number(
                    opportunity.conviction_score,
                    4,
                  )}
                </td>
              </tr>
            `;
          })
          .join("");
    }

    async function runRelativeValueScreen() {
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length < 2) {
        throw new Error(
          "Relative value analysis requires at least two instrument IDs.",
        );
      }

      const durationBucketWidth = Number(
        elements.relativeValueBucketWidth.value,
      );

      const minimumPeerCount = Number(
        elements.relativeValueMinimumPeers.value,
      );

      if (
        !Number.isFinite(durationBucketWidth)
        || durationBucketWidth <= 0
        || durationBucketWidth > 10
      ) {
        throw new Error(
          "Duration bucket width must be greater than zero and no more than 10.",
        );
      }

      if (
        !Number.isInteger(minimumPeerCount)
        || minimumPeerCount < 2
        || minimumPeerCount > 100
      ) {
        throw new Error(
          "Minimum peer count must be an integer between 2 and 100.",
        );
      }

      elements.runRelativeValueButton.disabled = true;
      elements.runRelativeValueButton.textContent =
        "Screening...";

      try {
        const payload = await request(
          "/relative-value/rank",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              instrument_ids: instrumentIds,
              duration_bucket_width:
                durationBucketWidth,
              minimum_peer_count:
                minimumPeerCount,
            }),
          },
        );

        renderRelativeValueResult(payload);

        log(
          `Relative value screen completed: `
          + `${payload.instrument_count} instruments, `
          + `${payload.opportunity_count} opportunities, `
          + `average spread `
          + `${number(payload.average_spread_bps, 2)} bp`,
        );
      } finally {
        elements.runRelativeValueButton.disabled = false;
        elements.runRelativeValueButton.textContent =
          "Run Relative Value Screen";
      }
    }


    const priceHistoryMetricDefinitions = {
      clean_price: {
        label: "Clean Price",
        formatter: (value) =>
          number(value, 4),
      },
      yield_to_maturity: {
        label: "Yield to Maturity",
        formatter: (value) =>
          percent(value),
      },
      g_spread_bps: {
        label: "G-Spread",
        formatter: (value) =>
          `${number(value, 2)} bp`,
      },
      modified_duration: {
        label: "Modified Duration",
        formatter: (value) =>
          number(value, 4),
      },
      convexity: {
        label: "Convexity",
        formatter: (value) =>
          number(value, 4),
      },
      quality_score: {
        label: "Quality Score",
        formatter: (value) =>
          number(value, 4),
      },
    };

    function formatPriceHistoryTime(value) {
      const date = new Date(value);

      if (Number.isNaN(date.getTime())) {
        return String(value || "—");
      }

      return date.toLocaleString();
    }

    function renderPriceHistoryChart() {
      const metric =
        elements.priceHistoryMetric.value;

      const definition =
        priceHistoryMetricDefinitions[metric];

      elements.priceHistoryChartTitle.textContent =
        definition.label;

      const values = currentPriceHistory
        .map((point) => ({
          value: Number(point[metric]),
          eventTime: point.event_time,
        }))
        .filter((point) =>
          Number.isFinite(point.value)
        );

      if (values.length === 0) {
        elements.priceHistoryChartRange.textContent =
          "No data";

        elements.priceHistoryChart.innerHTML = `
          <div class="price-history-empty">
            No valid observations were returned.
          </div>
        `;

        return;
      }

      const width = 1000;
      const height = 260;
      const left = 70;
      const right = 24;
      const top = 18;
      const bottom = 38;

      const chartWidth =
        width - left - right;

      const chartHeight =
        height - top - bottom;

      const minimum = Math.min(
        ...values.map((item) => item.value),
      );

      const maximum = Math.max(
        ...values.map((item) => item.value),
      );

      const rawRange = maximum - minimum;

      const padding =
        rawRange === 0
          ? Math.max(
              Math.abs(maximum) * 0.01,
              1,
            )
          : rawRange * 0.08;

      const chartMinimum =
        minimum - padding;

      const chartMaximum =
        maximum + padding;

      const chartRange =
        chartMaximum - chartMinimum;

      const xForIndex = (index) =>
        values.length === 1
          ? left + chartWidth / 2
          : left
            + (
              index
              / (values.length - 1)
            ) * chartWidth;

      const yForValue = (value) =>
        top
        + (
          1
          - (
            value - chartMinimum
          ) / chartRange
        ) * chartHeight;

      const points = values
        .map(
          (point, index) =>
            `${xForIndex(index)},`
            + `${yForValue(point.value)}`,
        )
        .join(" ");

      const gridLines = Array.from(
        { length: 5 },
        (_, index) => {
          const fraction = index / 4;

          const y =
            top
            + fraction * chartHeight;

          const value =
            chartMaximum
            - fraction * chartRange;

          return `
            <line
              class="price-history-chart-grid"
              x1="${left}"
              y1="${y}"
              x2="${left + chartWidth}"
              y2="${y}"
            />

            <text
              class="price-history-chart-label"
              x="${left - 10}"
              y="${y + 3}"
              text-anchor="end"
            >
              ${definition.formatter(value)}
            </text>
          `;
        },
      ).join("");

      const baseline =
        top + chartHeight;

      const areaPoints =
        `${left},${baseline} `
        + `${points} `
        + `${left + chartWidth},${baseline}`;

      elements.priceHistoryChartRange.textContent =
        `${definition.formatter(minimum)} – `
        + `${definition.formatter(maximum)}`;

      elements.priceHistoryChart.innerHTML = `
        <svg
          viewBox="0 0 ${width} ${height}"
          preserveAspectRatio="none"
        >
          ${gridLines}

          <polygon
            class="price-history-chart-area"
            points="${areaPoints}"
          />

          <polyline
            class="price-history-chart-line"
            points="${points}"
          />
        </svg>
      `;
    }

    function renderPriceHistory(payload) {
      currentPriceHistory =
        Array.isArray(payload)
          ? [...payload].sort(
              (left, right) =>
                new Date(
                  left.event_time,
                ).getTime()
                - new Date(
                  right.event_time,
                ).getTime(),
            )
          : [];

      elements
        .priceHistoryObservationCount
        .textContent =
          currentPriceHistory.length
            .toLocaleString();

      if (currentPriceHistory.length === 0) {
        elements.priceHistoryRows.innerHTML = `
          <tr>
            <td colspan="12" class="empty">
              No price history was returned.
            </td>
          </tr>
        `;

        renderPriceHistoryChart();

        return;
      }

      const latest =
        currentPriceHistory[
          currentPriceHistory.length - 1
        ];

      elements.priceHistoryLatestPrice.textContent =
        number(latest.clean_price, 4);

      elements.priceHistoryLatestYield.textContent =
        percent(latest.yield_to_maturity);

      elements.priceHistoryLatestSpread.textContent =
        `${number(
          latest.g_spread_bps,
          2,
        )} bp`;

      elements.priceHistoryLatestDuration.textContent =
        number(
          latest.modified_duration,
          4,
        );

      elements.priceHistoryLatestQuality.textContent =
        `${number(
          latest.quality_score,
          4,
        )} (${latest.quality_status})`;

      elements.priceHistoryCurveVersion.textContent =
        String(latest.curve_version);

      elements.priceHistoryModelVersion.textContent =
        String(latest.model_version);

      elements.priceHistoryRows.innerHTML =
        [...currentPriceHistory]
          .reverse()
          .map((point) => `
            <tr>
              <td>
                ${formatPriceHistoryTime(
                  point.event_time,
                )}
              </td>

              <td>
                ${number(
                  point.clean_price,
                  4,
                )}
              </td>

              <td>
                ${number(
                  point.dirty_price,
                  4,
                )}
              </td>

              <td>
                ${percent(
                  point.yield_to_maturity,
                )}
              </td>

              <td>
                ${number(
                  point.g_spread_bps,
                  2,
                )} bp
              </td>

              <td>
                ${number(
                  point.modified_duration,
                  4,
                )}
              </td>

              <td>
                ${number(
                  point.convexity,
                  4,
                )}
              </td>

              <td>
                ${number(
                  point.quality_score,
                  4,
                )}
              </td>

              <td>
                <span class="price-history-status">
                  ${point.quality_status}
                </span>
              </td>

              <td>
                ${point.curve_version}
              </td>

              <td>
                ${point.reference_version}
              </td>

              <td>
                ${point.model_version}
              </td>
            </tr>
          `)
          .join("");

      renderPriceHistoryChart();
    }

    async function runPriceHistory() {
      const instrumentId = Number(
        elements
          .priceHistoryInstrumentId
          .value,
      );

      const limit = Number(
        elements.priceHistoryLimit.value,
      );

      if (
        !Number.isInteger(instrumentId)
        || instrumentId < 1
      ) {
        throw new Error(
          "Instrument ID must be a positive integer.",
        );
      }

      if (
        !Number.isInteger(limit)
        || limit < 1
        || limit > 5000
      ) {
        throw new Error(
          "History limit must be between 1 and 5000.",
        );
      }

      elements
        .runPriceHistoryButton
        .disabled = true;

      elements
        .runPriceHistoryButton
        .textContent = "Loading...";

      try {
        const payload = await request(
          `/prices/${instrumentId}/history`
          + `?limit=${limit}`,
        );

        renderPriceHistory(payload);

        log(
          `Loaded ${payload.length} `
          + `price-history observations `
          + `for instrument ${instrumentId}`,
        );
      } finally {
        elements
          .runPriceHistoryButton
          .disabled = false;

        elements
          .runPriceHistoryButton
          .textContent =
            "Load Price History";
      }
    }


    function renderRiskDecomposition(payload) {
      const totalDv01 =
        Number(payload.total_dv01 || 0);

      elements
        .riskDecompositionInstrumentCount
        .textContent =
          Number(
            payload.instrument_count || 0,
          ).toLocaleString();

      elements
        .riskDecompositionMarketValue
        .textContent =
          currency(
            payload.total_market_value,
          );

      elements
        .riskDecompositionDv01
        .textContent =
          number(
            payload.total_dv01,
            2,
          );

      elements
        .riskDecompositionCs01
        .textContent =
          number(
            payload.total_cs01,
            2,
          );

      const keyRates =
        payload.portfolio_key_rate_dv01 || [];

      if (keyRates.length === 0) {
        elements
          .riskDecompositionKeyRateRows
          .innerHTML = `
            <tr>
              <td colspan="5" class="empty">
                No key-rate exposures returned.
              </td>
            </tr>
          `;
      } else {
        elements
          .riskDecompositionKeyRateRows
          .innerHTML =
            [...keyRates]
              .sort(
                (left, right) =>
                  Number(
                    left.tenor_years || 0,
                  )
                  - Number(
                    right.tenor_years || 0,
                  ),
              )
              .map((item) => {
                const share =
                  totalDv01 === 0
                    ? 0
                    : (
                        Number(
                          item.key_rate_dv01 || 0,
                        )
                        / totalDv01
                      ) * 100;

                return `
                  <tr>
                    <td>
                      ${item.tenor}
                    </td>

                    <td>
                      ${number(
                        item.tenor_years,
                        2,
                      )}
                    </td>

                    <td>
                      ${number(
                        item.key_rate_duration,
                        4,
                      )}
                    </td>

                    <td>
                      ${number(
                        item.key_rate_dv01,
                        2,
                      )}
                    </td>

                    <td class="
                      ${
                        share >= 30
                          ? "risk-share-high"
                          : ""
                      }
                    ">
                      ${share.toFixed(2)}%
                    </td>
                  </tr>
                `;
              })
              .join("");
      }

      const instruments =
        payload.instruments || [];

      if (instruments.length === 0) {
        elements
          .riskDecompositionInstrumentRows
          .innerHTML = `
            <tr>
              <td colspan="8" class="empty">
                No instrument risk returned.
              </td>
            </tr>
          `;

        return;
      }

      elements
        .riskDecompositionInstrumentRows
        .innerHTML =
          [...instruments]
            .sort(
              (left, right) =>
                Number(
                  right.aggregate_dv01 || 0,
                )
                - Number(
                  left.aggregate_dv01 || 0,
                ),
            )
            .map((item) => {
              const share =
                totalDv01 === 0
                  ? 0
                  : (
                      Number(
                        item.aggregate_dv01 || 0,
                      )
                      / totalDv01
                    ) * 100;

              return `
                <tr>
                  <td>
                    #${item.instrument_id}
                  </td>

                  <td>
                    ${number(
                      item.clean_price,
                      4,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.g_spread_bps,
                      2,
                    )} bp
                  </td>

                  <td>
                    ${number(
                      item.modified_duration,
                      4,
                    )}
                  </td>

                  <td>
                    ${currency(
                      item.market_value,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.aggregate_dv01,
                      2,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.cs01,
                      2,
                    )}
                  </td>

                  <td class="
                    ${
                      share >= 25
                        ? "risk-share-high"
                        : ""
                    }
                  ">
                    ${share.toFixed(2)}%
                  </td>
                </tr>
              `;
            })
            .join("");
    }

    async function runRiskDecomposition() {
      const instrumentIds =
        parseInstrumentIds();

      if (instrumentIds.length < 1) {
        throw new Error(
          "Risk decomposition requires at least one instrument ID.",
        );
      }

      const positionNotional = Number(
        elements
          .riskDecompositionNotional
          .value,
      );

      if (
        !Number.isFinite(positionNotional)
        || positionNotional <= 0
        || positionNotional > 1000000000
      ) {
        throw new Error(
          "Position notional must be greater than zero and no more than $1 billion.",
        );
      }

      elements
        .runRiskDecompositionButton
        .disabled = true;

      elements
        .runRiskDecompositionButton
        .textContent =
          "Running...";

      try {
        const payload = await request(
          "/risk/decomposition",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              instrument_ids:
                instrumentIds,
              position_notional:
                positionNotional,
            }),
          },
        );

        renderRiskDecomposition(
          payload,
        );

        log(
          `Risk decomposition completed: `
          + `${payload.instrument_count} `
          + `instruments, DV01 `
          + `${number(
            payload.total_dv01,
            2,
          )}, CS01 `
          + `${number(
            payload.total_cs01,
            2,
          )}`,
        );
      } finally {
        elements
          .runRiskDecompositionButton
          .disabled = false;

        elements
          .runRiskDecompositionButton
          .textContent =
            "Run Risk Decomposition";
      }
    }


    function carryRollValueClass(value) {
      const numeric = Number(value || 0);

      if (numeric > 0) {
        return "carry-roll-positive";
      }

      if (numeric < 0) {
        return "carry-roll-negative";
      }

      return "";
    }

    function carryRollClassificationClass(value) {
      return String(value || "")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9_-]+/g, "-");
    }

    function renderCarryRoll(payload) {
      const opportunities =
        payload.opportunities || [];

      elements
        .carryRollInstrumentCount
        .textContent =
          Number(
            payload.instrument_count || 0,
          ).toLocaleString();

      elements
        .carryRollHorizonResult
        .textContent =
          `${payload.horizon_months || 0}M`;

      elements
        .carryRollAverageReturn
        .textContent =
          `${number(
            payload.average_expected_return_percent,
            3,
          )}%`;

      if (opportunities.length === 0) {
        elements
          .carryRollTopOpportunity
          .textContent = "—";

        elements
          .carryRollRows
          .innerHTML = `
            <tr>
              <td colspan="14" class="empty">
                No carry and roll opportunities returned.
              </td>
            </tr>
          `;

        return;
      }

      const sorted =
        [...opportunities].sort(
          (left, right) =>
            Number(
              right.expected_total_return_percent || 0,
            )
            - Number(
              left.expected_total_return_percent || 0,
            ),
        );

      const top = sorted[0];

      elements
        .carryRollTopOpportunity
        .textContent =
          `#${top.instrument_id} `
          + `(${number(
            top.expected_total_return_percent,
            2,
          )}%)`;

      elements
        .carryRollRows
        .innerHTML =
          sorted
            .map((item) => {
              const classification =
                String(
                  item.classification || "Unknown",
                );

              return `
                <tr>
                  <td>
                    #${item.instrument_id}
                  </td>

                  <td>
                    ${number(
                      item.clean_price,
                      4,
                    )}
                  </td>

                  <td>
                    ${percent(
                      item.yield_to_maturity,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.g_spread_bps,
                      2,
                    )} bp
                  </td>

                  <td>
                    ${number(
                      item.modified_duration,
                      3,
                    )}
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.coupon_carry_return_percent,
                    )}
                  ">
                    ${signedNumber(
                      item.coupon_carry_return_percent,
                      3,
                    )}%
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.financing_cost_return_percent,
                    )}
                  ">
                    ${signedNumber(
                      item.financing_cost_return_percent,
                      3,
                    )}%
                  </td>

                  <td>
                    ${signedNumber(
                      item.treasury_roll_down_bps,
                      2,
                    )} bp
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.treasury_roll_return_percent,
                    )}
                  ">
                    ${signedNumber(
                      item.treasury_roll_return_percent,
                      3,
                    )}%
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.spread_normalization_return_percent,
                    )}
                  ">
                    ${signedNumber(
                      item.spread_normalization_return_percent,
                      3,
                    )}%
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.expected_total_return_percent,
                    )}
                  ">
                    <strong>
                      ${signedNumber(
                        item.expected_total_return_percent,
                        3,
                      )}%
                    </strong>
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.expected_pnl_per_million,
                    )}
                  ">
                    ${signedCurrency(
                      item.expected_pnl_per_million,
                    )}
                  </td>

                  <td>
                    <span
                      class="
                        carry-roll-classification
                        ${carryRollClassificationClass(
                          classification,
                        )}
                      "
                    >
                      ${classification}
                    </span>
                  </td>

                  <td>
                    ${number(
                      item.conviction_score,
                      3,
                    )}
                  </td>
                </tr>
              `;
            })
            .join("");
    }

    async function runCarryRoll() {
      const instrumentIds =
        parseInstrumentIds();

      if (instrumentIds.length < 2) {
        throw new Error(
          "Carry & Roll ranking requires at least two instrument IDs.",
        );
      }

      const horizonMonths = Number(
        elements.carryRollHorizon.value,
      );

      const financingRate = Number(
        elements.carryRollFinancingRate.value,
      );

      const normalization = Number(
        elements.carryRollNormalization.value,
      );

      if (
        !Number.isInteger(horizonMonths)
        || horizonMonths < 1
        || horizonMonths > 24
      ) {
        throw new Error(
          "Horizon must be between 1 and 24 months.",
        );
      }

      if (
        !Number.isFinite(financingRate)
        || financingRate < -0.05
        || financingRate > 0.25
      ) {
        throw new Error(
          "Financing rate must be between -5% and 25%.",
        );
      }

      if (
        !Number.isFinite(normalization)
        || normalization < 0
        || normalization > 1
      ) {
        throw new Error(
          "Spread normalization fraction must be between 0 and 1.",
        );
      }

      elements
        .runCarryRollButton
        .disabled = true;

      elements
        .runCarryRollButton
        .textContent =
          "Ranking...";

      try {
        const payload = await request(
          "/carry-roll/rank",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              instrument_ids:
                instrumentIds,
              horizon_months:
                horizonMonths,
              annual_financing_rate:
                financingRate,
              expected_spread_normalization_fraction:
                normalization,
            }),
          },
        );

        renderCarryRoll(
          payload,
        );

        log(
          `Carry & Roll completed: `
          + `${payload.instrument_count} instruments, `
          + `${payload.horizon_months}M horizon, `
          + `average expected return `
          + `${number(
            payload.average_expected_return_percent,
            3,
          )}%`,
        );
      } finally {
        elements
          .runCarryRollButton
          .disabled = false;

        elements
          .runCarryRollButton
          .textContent =
            "Rank Carry & Roll";
      }
    }


    function stressValueClass(value) {
      const numeric = Number(value || 0);

      if (numeric > 0) {
        return "stress-positive";
      }

      if (numeric < 0) {
        return "stress-negative";
      }

      return "";
    }

    function renderStressTest(payload) {
      const instruments =
        payload.instruments || [];

      elements
        .stressInstrumentCount
        .textContent =
          Number(
            payload.instrument_count || 0,
          ).toLocaleString();

      elements
        .stressMarketValue
        .textContent =
          currency(
            payload.total_market_value,
          );

      elements
        .stressTreasuryPnl
        .textContent =
          signedCurrency(
            payload.total_treasury_pnl,
          );

      elements
        .stressTreasuryPnl
        .className =
          stressValueClass(
            payload.total_treasury_pnl,
          );

      elements
        .stressCreditPnl
        .textContent =
          signedCurrency(
            payload.total_credit_pnl,
          );

      elements
        .stressCreditPnl
        .className =
          stressValueClass(
            payload.total_credit_pnl,
          );

      elements
        .stressTotalPnl
        .textContent =
          signedCurrency(
            payload.total_pnl,
          );

      elements
        .stressTotalPnl
        .className =
          stressValueClass(
            payload.total_pnl,
          );

      if (instruments.length === 0) {
        elements
          .stressTestRows
          .innerHTML = `
            <tr>
              <td colspan="6" class="empty">
                No stress results returned.
              </td>
            </tr>
          `;

        return;
      }

      elements
        .stressTestRows
        .innerHTML =
          [...instruments]
            .sort(
              (left, right) =>
                Math.abs(
                  Number(
                    right.total_pnl || 0,
                  ),
                )
                - Math.abs(
                  Number(
                    left.total_pnl || 0,
                  ),
                ),
            )
            .map((item) => {
              const marketValue =
                Number(
                  item.market_value || 0,
                );

              const totalPnl =
                Number(
                  item.total_pnl || 0,
                );

              const pnlPercent =
                marketValue === 0
                  ? 0
                  : (
                      totalPnl
                      / marketValue
                    ) * 100;

              return `
                <tr>
                  <td>
                    #${item.instrument_id}
                  </td>

                  <td>
                    ${currency(
                      item.market_value,
                    )}
                  </td>

                  <td class="
                    ${stressValueClass(
                      item.treasury_pnl,
                    )}
                  ">
                    ${signedCurrency(
                      item.treasury_pnl,
                    )}
                  </td>

                  <td class="
                    ${stressValueClass(
                      item.credit_pnl,
                    )}
                  ">
                    ${signedCurrency(
                      item.credit_pnl,
                    )}
                  </td>

                  <td class="
                    ${stressValueClass(
                      item.total_pnl,
                    )}
                  ">
                    <strong>
                      ${signedCurrency(
                        item.total_pnl,
                      )}
                    </strong>
                  </td>

                  <td class="
                    ${stressValueClass(
                      pnlPercent,
                    )}
                  ">
                    ${signedNumber(
                      pnlPercent,
                      3,
                    )}%
                  </td>
                </tr>
              `;
            })
            .join("");
    }

    async function runStressTest() {
      const instrumentIds =
        parseInstrumentIds();

      if (instrumentIds.length < 1) {
        throw new Error(
          "Stress testing requires at least one instrument ID.",
        );
      }

      const positionNotional = Number(
        elements
          .stressPositionNotional
          .value,
      );

      const treasuryParallel = Number(
        elements
          .stressTreasuryParallel
          .value,
      );

      const treasury2Y = Number(
        elements
          .stressTreasury2Y
          .value,
      );

      const treasury5Y = Number(
        elements
          .stressTreasury5Y
          .value,
      );

      const treasury10Y = Number(
        elements
          .stressTreasury10Y
          .value,
      );

      const treasury30Y = Number(
        elements
          .stressTreasury30Y
          .value,
      );

      const creditParallel = Number(
        elements
          .stressCreditParallel
          .value,
      );

      if (
        !Number.isFinite(positionNotional)
        || positionNotional <= 0
        || positionNotional > 1000000000
      ) {
        throw new Error(
          "Position notional must be greater than zero and no more than $1 billion.",
        );
      }

      const treasuryShocks = [
        treasuryParallel,
        treasury2Y,
        treasury5Y,
        treasury10Y,
        treasury30Y,
      ];

      if (
        treasuryShocks.some(
          (value) =>
            !Number.isFinite(value)
            || value < -1000
            || value > 1000,
        )
      ) {
        throw new Error(
          "Treasury shocks must be between -1000 and 1000 bp.",
        );
      }

      if (
        !Number.isFinite(creditParallel)
        || creditParallel < -2000
        || creditParallel > 2000
      ) {
        throw new Error(
          "Credit shock must be between -2000 and 2000 bp.",
        );
      }

      elements
        .runStressTestButton
        .disabled = true;

      elements
        .runStressTestButton
        .textContent =
          "Running...";

      try {
        const payload = await request(
          "/stress/run",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              instrument_ids:
                instrumentIds,
              position_notional:
                positionNotional,
              scenario: {
                treasury_parallel_bps:
                  treasuryParallel,
                treasury_2y_bps:
                  treasury2Y,
                treasury_5y_bps:
                  treasury5Y,
                treasury_10y_bps:
                  treasury10Y,
                treasury_30y_bps:
                  treasury30Y,
                credit_parallel_bps:
                  creditParallel,
              },
            }),
          },
        );

        renderStressTest(
          payload,
        );

        log(
          `Stress test completed: `
          + `${payload.instrument_count} instruments, `
          + `Treasury P&L `
          + `${signedCurrency(
            payload.total_treasury_pnl,
          )}, credit P&L `
          + `${signedCurrency(
            payload.total_credit_pnl,
          )}, total `
          + `${signedCurrency(
            payload.total_pnl,
          )}`,
        );
      } finally {
        elements
          .runStressTestButton
          .disabled = false;

        elements
          .runStressTestButton
          .textContent =
            "Run Stress Test";
      }
    }


    function renderPortfolioRisk(payload) {
      const positions =
        payload.positions || [];

      elements
        .portfolioRiskPositionCount
        .textContent =
          Number(
            payload.position_count || 0,
          ).toLocaleString();

      elements
        .portfolioRiskTotalFaceValue
        .textContent =
          currency(
            payload.total_face_value,
          );

      elements
        .portfolioRiskMarketValue
        .textContent =
          currency(
            payload.total_market_value,
          );

      elements
        .portfolioRiskWeightedYield
        .textContent =
          percent(
            payload.weighted_yield_to_maturity,
          );

      elements
        .portfolioRiskWeightedSpread
        .textContent =
          `${number(
            payload.weighted_g_spread_bps,
            2,
          )} bp`;

      elements
        .portfolioRiskWeightedDuration
        .textContent =
          number(
            payload.weighted_modified_duration,
            4,
          );

      elements
        .portfolioRiskWeightedConvexity
        .textContent =
          number(
            payload.weighted_convexity,
            4,
          );

      elements
        .portfolioRiskTotalDv01
        .textContent =
          number(
            payload.total_dv01,
            2,
          );

      elements
        .portfolioRiskConvexityContribution
        .textContent =
          number(
            payload.total_convexity_contribution,
            2,
          );

      if (positions.length === 0) {
        elements
          .portfolioRiskRows
          .innerHTML = `
            <tr>
              <td colspan="11" class="empty">
                No position risk returned.
              </td>
            </tr>
          `;

        return;
      }

      elements
        .portfolioRiskRows
        .innerHTML =
          [...positions]
            .sort(
              (left, right) =>
                Number(
                  right.market_value_weight || 0,
                )
                - Number(
                  left.market_value_weight || 0,
                ),
            )
            .map((item) => {
              const weight =
                Number(
                  item.market_value_weight || 0,
                ) * 100;

              return `
                <tr>
                  <td>
                    #${item.instrument_id}
                  </td>

                  <td>
                    ${currency(
                      item.face_value,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.clean_price,
                      4,
                    )}
                  </td>

                  <td>
                    ${currency(
                      item.market_value,
                    )}
                  </td>

                  <td>
                    ${percent(
                      item.yield_to_maturity,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.g_spread_bps,
                      2,
                    )} bp
                  </td>

                  <td>
                    ${number(
                      item.modified_duration,
                      4,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.convexity,
                      4,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.dv01,
                      2,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.convexity_contribution,
                      2,
                    )}
                  </td>

                  <td class="
                    ${
                      weight >= 25
                        ? "portfolio-risk-weight-high"
                        : ""
                    }
                  ">
                    ${weight.toFixed(2)}%
                  </td>
                </tr>
              `;
            })
            .join("");
    }

    async function runPortfolioRisk() {
      const instrumentIds =
        parseInstrumentIds();

      if (instrumentIds.length < 1) {
        throw new Error(
          "Portfolio risk requires at least one instrument ID.",
        );
      }

      const faceValue = Number(
        elements
          .portfolioRiskFaceValue
          .value,
      );

      if (
        !Number.isFinite(faceValue)
        || faceValue <= 0
        || faceValue > 1000000000
      ) {
        throw new Error(
          "Face value must be greater than zero and no more than $1 billion.",
        );
      }

      elements
        .runPortfolioRiskButton
        .disabled = true;

      elements
        .runPortfolioRiskButton
        .textContent =
          "Calculating...";

      try {
        const payload = await request(
          "/portfolio/risk",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              positions:
                instrumentIds.map(
                  (instrumentId) => ({
                    instrument_id:
                      instrumentId,
                    face_value:
                      faceValue,
                  }),
                ),
            }),
          },
        );

        renderPortfolioRisk(
          payload,
        );

        log(
          `Portfolio risk completed: `
          + `${payload.position_count} positions, `
          + `market value `
          + `${currency(
            payload.total_market_value,
          )}, DV01 `
          + `${number(
            payload.total_dv01,
            2,
          )}`,
        );
      } finally {
        elements
          .runPortfolioRiskButton
          .disabled = false;

        elements
          .runPortfolioRiskButton
          .textContent =
            "Calculate Portfolio Risk";
      }
    }


    function marketQualityClass(score) {
      const value = Number(score || 0);

      if (value >= 0.9) {
        return "market-quality-good";
      }

      if (value >= 0.8) {
        return "market-quality-warning";
      }

      return "market-quality-bad";
    }

    function renderMarketOverviewRows() {
      const query = String(
        elements.marketOverviewSearch.value || "",
      )
        .trim()
        .toLowerCase();

      const rows = currentMarketOverview.filter(
        (item) => {
          if (!query) {
            return true;
          }

          return [
            item.instrument_id,
            item.quality_status,
            item.curve_version,
            item.reference_version,
          ]
            .map((value) =>
              String(value ?? "")
                .toLowerCase()
            )
            .some((value) =>
              value.includes(query)
            );
        },
      );

      elements
        .marketOverviewVisibleCount
        .textContent =
          rows.length.toLocaleString();

      if (rows.length === 0) {
        elements
          .marketOverviewRows
          .innerHTML = `
            <tr>
              <td colspan="12" class="empty">
                No market rows match the current filter.
              </td>
            </tr>
          `;

        return;
      }

      elements
        .marketOverviewRows
        .innerHTML =
          rows
            .map((item) => `
              <tr>
                <td>
                  #${item.instrument_id}
                </td>

                <td>
                  ${number(
                    item.clean_price,
                    4,
                  )}
                </td>

                <td>
                  ${number(
                    item.dirty_price,
                    4,
                  )}
                </td>

                <td>
                  ${percent(
                    item.yield_to_maturity,
                  )}
                </td>

                <td>
                  ${number(
                    item.g_spread_bps,
                    2,
                  )} bp
                </td>

                <td>
                  ${number(
                    item.modified_duration,
                    4,
                  )}
                </td>

                <td>
                  ${number(
                    item.convexity,
                    4,
                  )}
                </td>

                <td class="
                  ${marketQualityClass(
                    item.quality_score,
                  )}
                ">
                  ${number(
                    item.quality_score,
                    3,
                  )}
                </td>

                <td>
                  ${item.quality_status}
                </td>

                <td>
                  ${item.curve_version}
                </td>

                <td>
                  ${item.reference_version}
                </td>

                <td>
                  ${formatPriceHistoryTime(
                    item.event_time,
                  )}
                </td>
              </tr>
            `)
            .join("");
    }

    function renderMarketSummary(payload) {
      elements
        .marketSummaryInstrumentCount
        .textContent =
          Number(
            payload.instrument_count || 0,
          ).toLocaleString();

      elements
        .marketSummaryAveragePrice
        .textContent =
          number(
            payload.average_clean_price,
            4,
          );

      elements
        .marketSummaryAverageYield
        .textContent =
          percent(
            payload.average_yield_to_maturity,
          );

      elements
        .marketSummaryAverageSpread
        .textContent =
          `${number(
            payload.average_g_spread_bps,
            2,
          )} bp`;

      elements
        .marketSummaryWidestInstrument
        .textContent =
          payload.widest_instrument_id == null
            ? "—"
            : `#${payload.widest_instrument_id}`;

      elements
        .marketSummaryWidestSpread
        .textContent =
          payload.widest_g_spread_bps == null
            ? "—"
            : `${number(
                payload.widest_g_spread_bps,
                2,
              )} bp`;
    }

    async function loadMarketOverview() {
      const limit = Number(
        elements.marketOverviewLimit.value,
      );

      const minimumQuality = Number(
        elements.marketOverviewQuality.value,
      );

      if (
        !Number.isInteger(limit)
        || limit < 1
        || limit > 10000
      ) {
        throw new Error(
          "Instrument limit must be between 1 and 10000.",
        );
      }

      if (
        !Number.isFinite(minimumQuality)
        || minimumQuality < 0
        || minimumQuality > 1
      ) {
        throw new Error(
          "Minimum quality score must be between 0 and 1.",
        );
      }

      elements
        .loadMarketOverviewButton
        .disabled = true;

      elements
        .loadMarketOverviewButton
        .textContent =
          "Loading...";

      try {
        const [
          summary,
          latestPrices,
        ] = await Promise.all([
          request(
            "/market/summary",
          ),
          request(
            "/prices/latest"
            + `?limit=${limit}`
            + `&minimum_quality_score=${minimumQuality}`,
          ),
        ]);

        currentMarketOverview =
          Array.isArray(latestPrices)
            ? [...latestPrices].sort(
                (left, right) =>
                  Number(
                    right.g_spread_bps || 0,
                  )
                  - Number(
                    left.g_spread_bps || 0,
                  ),
              )
            : [];

        renderMarketSummary(
          summary,
        );

        renderMarketOverviewRows();

        log(
          `Market overview loaded: `
          + `${summary.instrument_count} instruments, `
          + `${currentMarketOverview.length} latest prices, `
          + `average spread `
          + `${number(
            summary.average_g_spread_bps,
            2,
          )} bp`,
        );
      } finally {
        elements
          .loadMarketOverviewButton
          .disabled = false;

        elements
          .loadMarketOverviewButton
          .textContent =
            "Load Market Overview";
      }
    }


    function renderMarketStreamStatus(payload) {
      const running =
        Boolean(payload.running);

      elements
        .streamStatusRunning
        .textContent =
          running
            ? "Running"
            : "Stopped";

      elements
        .streamStatusRunning
        .className =
          running
            ? "stream-running"
            : "stream-stopped";

      elements
        .streamStatusClients
        .textContent =
          Number(
            payload.client_count || 0,
          ).toLocaleString();

      elements
        .streamStatusInstruments
        .textContent =
          Number(
            payload.instrument_count || 0,
          ).toLocaleString();

      elements
        .streamStatusInterval
        .textContent =
          payload.interval_ms == null
            ? "—"
            : `${payload.interval_ms} ms`;

      elements
        .streamStatusSequence
        .textContent =
          Number(
            payload.sequence || 0,
          ).toLocaleString();
    }

    async function refreshMarketStreamStatus() {
      const payload = await request(
        "/stream/status",
      );

      renderMarketStreamStatus(
        payload,
      );

      return payload;
    }

    async function startMarketStream() {
      const instrumentIds =
        parseInstrumentIds();

      if (instrumentIds.length < 1) {
        throw new Error(
          "Starting the market stream requires at least one instrument ID.",
        );
      }

      const intervalMs = Number(
        elements.streamIntervalMs.value,
      );

      const volatilityBps = Number(
        elements.streamVolatilityBps.value,
      );

      if (
        !Number.isInteger(intervalMs)
        || intervalMs < 100
        || intervalMs > 60000
      ) {
        throw new Error(
          "Stream interval must be between 100 and 60000 ms.",
        );
      }

      if (
        !Number.isFinite(volatilityBps)
        || volatilityBps < 0
        || volatilityBps > 100
      ) {
        throw new Error(
          "Stream volatility must be between 0 and 100 bp.",
        );
      }

      elements
        .startMarketStreamButton
        .disabled = true;

      elements
        .startMarketStreamButton
        .textContent =
          "Starting...";

      try {
        const payload = await request(
          "/stream/start",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              instrument_ids:
                instrumentIds,
              interval_ms:
                intervalMs,
              volatility_bps:
                volatilityBps,
            }),
          },
        );

        renderMarketStreamStatus(
          payload,
        );

        log(
          `Market stream started: `
          + `${payload.instrument_count} instruments, `
          + `${payload.interval_ms} ms interval`,
        );
      } finally {
        elements
          .startMarketStreamButton
          .disabled = false;

        elements
          .startMarketStreamButton
          .textContent =
            "Start Stream";
      }
    }

    async function stopMarketStream() {
      elements
        .stopMarketStreamButton
        .disabled = true;

      elements
        .stopMarketStreamButton
        .textContent =
          "Stopping...";

      try {
        const payload = await request(
          "/stream/stop",
          {
            method: "POST",
          },
        );

        renderMarketStreamStatus(
          payload,
        );

        log(
          "Market stream stopped.",
        );
      } finally {
        elements
          .stopMarketStreamButton
          .disabled = false;

        elements
          .stopMarketStreamButton
          .textContent =
            "Stop Stream";
      }
    }

    function formatReplayDuration(
      firstEventTime,
      lastEventTime,
    ) {
      const first =
        new Date(firstEventTime);

      const last =
        new Date(lastEventTime);

      if (
        Number.isNaN(first.getTime())
        || Number.isNaN(last.getTime())
      ) {
        return "—";
      }

      const seconds =
        Math.max(
          0,
          (
            last.getTime()
            - first.getTime()
          ) / 1000,
        );

      if (seconds < 60) {
        return `${seconds.toFixed(1)} sec`;
      }

      if (seconds < 3600) {
        return `${(seconds / 60).toFixed(1)} min`;
      }

      return `${(seconds / 3600).toFixed(2)} hr`;
    }

    async function loadReplayScenarios() {
      elements
        .loadReplayScenariosButton
        .disabled = true;

      elements
        .loadReplayScenariosButton
        .textContent =
          "Loading...";

      try {
        const payload = await request(
          "/replay/scenarios",
        );

        const scenarios =
          Array.isArray(payload)
            ? payload
            : [];

        if (scenarios.length === 0) {
          elements
            .replayScenarioRows
            .innerHTML = `
              <tr>
                <td colspan="5" class="empty">
                  No replay scenarios are currently available.
                </td>
              </tr>
            `;

          return;
        }

        elements
          .replayScenarioRows
          .innerHTML =
            scenarios
              .sort(
                (left, right) =>
                  Number(
                    right.event_count || 0,
                  )
                  - Number(
                    left.event_count || 0,
                  ),
              )
              .map((scenario) => `
                <tr>
                  <td>
                    ${scenario.scenario_name}
                  </td>

                  <td>
                    ${Number(
                      scenario.event_count || 0,
                    ).toLocaleString()}
                  </td>

                  <td>
                    ${formatPriceHistoryTime(
                      scenario.first_event_time,
                    )}
                  </td>

                  <td>
                    ${formatPriceHistoryTime(
                      scenario.last_event_time,
                    )}
                  </td>

                  <td>
                    ${formatReplayDuration(
                      scenario.first_event_time,
                      scenario.last_event_time,
                    )}
                  </td>
                </tr>
              `)
              .join("");

        log(
          `Loaded ${scenarios.length} replay scenarios.`,
        );
      } finally {
        elements
          .loadReplayScenariosButton
          .disabled = false;

        elements
          .loadReplayScenariosButton
          .textContent =
            "Load Replay Scenarios";
      }
    }

    function exportSnapshot() {
      const snapshot = {
        exported_at: new Date().toISOString(),
        sequence: state.sequence,
        controls: {
          instrument_ids: parseInstrumentIds(),
          position_notional:
            Number(elements.positionNotional.value),
          treasury_shift_bps:
            Number(elements.treasuryShift.value),
          spread_shift_bps:
            Number(elements.spreadShift.value),
          liquidity_haircut_percent:
            Number(elements.liquidityHaircut.value),
          downgrade_notches:
            Number(elements.downgradeNotches.value),
        },
        prices: Array.from(state.prices.values()),
        scenario: state.scenario,
      };

      const blob = new Blob(
        [JSON.stringify(snapshot, null, 2)],
        {
          type: "application/json",
        },
      );

      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");

      anchor.href = url;
      anchor.download =
        `mercator-snapshot-${Date.now()}.json`;

      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      URL.revokeObjectURL(url);
      log("Snapshot exported");
    }

    async function handleAction(action) {
      try {
        await action();
      } catch (error) {
        log(`ERROR: ${error.message}`);
        setConnection("error", "Request failed");
      }
    }

    elements.startButton.addEventListener(
      "click",
      () => handleAction(startStream),
    );

    elements.stopButton.addEventListener(
      "click",
      () => handleAction(stopStream),
    );

    elements.scenarioButton.addEventListener(
      "click",
      () => handleAction(runScenario),
    );

    elements.exportButton.addEventListener(
      "click",
      exportSnapshot,
    );


    elements.runOptimizerButton.addEventListener(
      "click",
      () => handleAction(runStandardOptimizer),
    );


    elements.runRiskOptimizerButton.addEventListener(
      "click",
      () => handleAction(runRiskBudgetOptimizer),
    );


    elements.runHistoricalVarButton.addEventListener(
      "click",
      () => handleAction(runHistoricalVar),
    );


    elements.runHedgeRecommendationsButton.addEventListener(
      "click",
      () => handleAction(runHedgeRecommendations),
    );


    elements.runRelativeValueButton.addEventListener(
      "click",
      () => handleAction(runRelativeValueScreen),
    );


    elements.runPriceHistoryButton.addEventListener(
      "click",
      () => handleAction(runPriceHistory),
    );

    elements.priceHistoryMetric.addEventListener(
      "change",
      renderPriceHistoryChart,
    );


    elements
      .runRiskDecompositionButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            runRiskDecomposition,
          ),
      );


    elements
      .runCarryRollButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            runCarryRoll,
          ),
      );


    elements
      .runStressTestButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            runStressTest,
          ),
      );


    elements
      .runPortfolioRiskButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            runPortfolioRisk,
          ),
      );


    elements
      .loadMarketOverviewButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            loadMarketOverview,
          ),
      );

    elements
      .marketOverviewSearch
      .addEventListener(
        "input",
        renderMarketOverviewRows,
      );


    elements
      .startMarketStreamButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            startMarketStream,
          ),
      );

    elements
      .stopMarketStreamButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            stopMarketStream,
          ),
      );

    elements
      .refreshMarketStreamStatusButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            refreshMarketStreamStatus,
          ),
      );

    elements
      .loadReplayScenariosButton
      .addEventListener(
        "click",
        () =>
          handleAction(
            loadReplayScenarios,
          ),
      );

    elements.positionNotional.addEventListener(
      "input",
      render,
    );

    render();


    const workspaceButtons = document.querySelectorAll(
      ".workspace-nav button[data-target]",
    );

    workspaceButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const target = document.getElementById(
          button.dataset.target,
        );

        if (!target) {
          return;
        }

        workspaceButtons.forEach((item) => {
          item.classList.remove("active");
        });

        button.classList.add("active");

        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });
    });
