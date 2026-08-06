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
  markResultFresh(
    "historicalVar",
  );

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
  markResultFresh(
    "hedgeRecommendations",
  );

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



    function renderRiskDecomposition(payload) {
  markResultFresh(
    "riskDecomposition",
  );

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
                    #${instrumentLinkHtml(item.instrument_id)}
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
  markResultFresh(
    "stressTest",
  );

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
                    #${instrumentLinkHtml(item.instrument_id)}
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
