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

      toastError(
        error?.message
          || String(error),
        "Action failed",
      );

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


// ============================================================
// Sidebar navigation
// ============================================================

function initializeSidebarNavigation() {
  const links = Array.from(
    document.querySelectorAll(
      ".sidebar-link",
    ),
  );

  if (links.length === 0) {
    return;
  }

  const targets = links
    .map((link) => {
      const selector =
        link.getAttribute("href");

      if (
        !selector
        || !selector.startsWith("#")
      ) {
        return null;
      }

      const element =
        document.querySelector(selector);

      if (!element) {
        return null;
      }

      return {
        link,
        element,
      };
    })
    .filter(Boolean);

  function updateActiveSidebarLink() {
    const position =
      window.scrollY + 160;

    let active =
      targets[0];

    for (const target of targets) {
      if (
        target.element.offsetTop
        <= position
      ) {
        active = target;
      }
    }

    for (const target of targets) {
      target.link.classList.toggle(
        "active",
        target === active,
      );
    }
  }

  window.addEventListener(
    "scroll",
    updateActiveSidebarLink,
    {
      passive: true,
    },
  );

  updateActiveSidebarLink();
}

initializeSidebarNavigation();


// ============================================================
// System Health
// ============================================================

async function refreshSystemHealth() {
  const apiElement =
    document.getElementById(
      "systemHealthApi",
    );

  const streamElement =
    document.getElementById(
      "systemHealthStream",
    );

  const clientsElement =
    document.getElementById(
      "systemHealthClients",
    );

  const streamInstrumentsElement =
    document.getElementById(
      "systemHealthStreamInstruments",
    );

  const sequenceElement =
    document.getElementById(
      "systemHealthSequence",
    );

  const marketCountElement =
    document.getElementById(
      "systemHealthMarketCount",
    );

  const lastRefreshElement =
    document.getElementById(
      "systemHealthLastRefresh",
    );

  const button =
    document.getElementById(
      "refreshSystemHealthButton",
    );

  if (
    !apiElement
    || !streamElement
    || !clientsElement
    || !streamInstrumentsElement
    || !sequenceElement
    || !marketCountElement
    || !lastRefreshElement
  ) {
    return;
  }

  if (button) {
    button.disabled = true;
    button.textContent = "Refreshing...";
  }

  try {
    const [
      healthResult,
      streamResult,
      marketResult,
    ] = await Promise.allSettled([
      request("/health"),
      request("/stream/status"),
      request("/market/summary"),
    ]);

    if (
      healthResult.status === "fulfilled"
      && healthResult.value.status === "ok"
    ) {
      apiElement.textContent = "Healthy";
      apiElement.className =
        "system-health-value system-health-good";
    } else {
      apiElement.textContent = "Unavailable";
      apiElement.className =
        "system-health-value system-health-bad";
    }

    if (
      streamResult.status === "fulfilled"
    ) {
      const stream =
        streamResult.value;

      streamElement.textContent =
        stream.running
          ? "Running"
          : "Stopped";

      streamElement.className =
        stream.running
          ? "system-health-value system-health-good"
          : "system-health-value system-health-warning";

      clientsElement.textContent =
        Number(
          stream.client_count || 0,
        ).toLocaleString();

      streamInstrumentsElement.textContent =
        Number(
          stream.instrument_count || 0,
        ).toLocaleString();

      sequenceElement.textContent =
        Number(
          stream.sequence || 0,
        ).toLocaleString();
    } else {
      streamElement.textContent =
        "Unavailable";

      streamElement.className =
        "system-health-value system-health-bad";

      clientsElement.textContent = "—";
      streamInstrumentsElement.textContent = "—";
      sequenceElement.textContent = "—";
    }

    if (
      marketResult.status === "fulfilled"
    ) {
      marketCountElement.textContent =
        Number(
          marketResult.value.instrument_count || 0,
        ).toLocaleString();
    } else {
      marketCountElement.textContent =
        "—";
    }

    lastRefreshElement.textContent =
      new Date().toLocaleTimeString();
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Refresh";
    }
  }
}

const refreshSystemHealthButton =
  document.getElementById(
    "refreshSystemHealthButton",
  );

if (refreshSystemHealthButton) {
  refreshSystemHealthButton.addEventListener(
    "click",
    () =>
      handleAction(
        refreshSystemHealth,
      ),
  );
}

refreshSystemHealth();

setInterval(
  () => {
    refreshSystemHealth().catch(
      () => {},
    );
  },
  15000,
);


// ============================================================
// Collapsible panels
// ============================================================

function setPanelCollapsed(
  card,
  collapsed,
) {
  const button =
    card.querySelector(
      ".panel-collapse-button",
    );

  card.classList.toggle(
    "panel-collapsed",
    collapsed,
  );

  if (!button) {
    return;
  }

  button.setAttribute(
    "aria-expanded",
    String(!collapsed),
  );

  button.textContent =
    collapsed
      ? "+"
      : "−";

  button.title =
    collapsed
      ? "Expand panel"
      : "Collapse panel";
}

function initializeCollapsiblePanels() {
  const buttons = Array.from(
    document.querySelectorAll(
      ".panel-collapse-button",
    ),
  );

  for (const button of buttons) {
    button.addEventListener(
      "click",
      () => {
        const card =
          button.closest(".card");

        if (!card) {
          return;
        }

        const collapsed =
          !card.classList.contains(
            "panel-collapsed",
          );

        setPanelCollapsed(
          card,
          collapsed,
        );
      },
    );
  }

  const expandAll =
    document.getElementById(
      "expandAllPanelsButton",
    );

  const collapseAll =
    document.getElementById(
      "collapseAllPanelsButton",
    );

  if (expandAll) {
    expandAll.addEventListener(
      "click",
      () => {
        document
          .querySelectorAll(".card")
          .forEach((card) => {
            setPanelCollapsed(
              card,
              false,
            );
          });
      },
    );
  }

  if (collapseAll) {
    collapseAll.addEventListener(
      "click",
      () => {
        document
          .querySelectorAll(".card")
          .forEach((card) => {
            setPanelCollapsed(
              card,
              true,
            );
          });
      },
    );
  }
}

initializeCollapsiblePanels();


// ============================================================
// Persistent UI state
// ============================================================

const MERCATOR_UI_STATE_KEY =
  "mercator.workbench.ui.v1";

const persistentInputIds = [
  "instrumentIds",
  "positionNotional",

  "priceHistoryInstrumentId",
  "priceHistoryLimit",
  "priceHistoryMetric",

  "riskDecompositionNotional",

  "carryRollHorizon",
  "carryRollFinancingRate",
  "carryRollNormalization",

  "stressPositionNotional",
  "stressTreasuryParallel",
  "stressTreasury2Y",
  "stressTreasury5Y",
  "stressTreasury10Y",
  "stressTreasury30Y",
  "stressCreditParallel",

  "portfolioRiskFaceValue",

  "marketOverviewLimit",
  "marketOverviewQuality",
  "marketOverviewSearch",

  "streamIntervalMs",
  "streamVolatilityBps",

  "hedgePositionNotional",
  "hedgeRatio",
  "includeCreditHedge",

  "relativeValueBucketWidth",
  "relativeValueMinimumPeers",
];

function readWorkbenchUiState() {
  try {
    const raw =
      window.localStorage.getItem(
        MERCATOR_UI_STATE_KEY,
      );

    if (!raw) {
      return {
        inputs: {},
        collapsedPanels: [],
      };
    }

    const parsed =
      JSON.parse(raw);

    return {
      inputs:
        parsed.inputs
        && typeof parsed.inputs === "object"
          ? parsed.inputs
          : {},

      collapsedPanels:
        Array.isArray(
          parsed.collapsedPanels,
        )
          ? parsed.collapsedPanels
          : [],
    };
  } catch {
    return {
      inputs: {},
      collapsedPanels: [],
    };
  }
}

function panelPersistenceKey(
  card,
  index,
) {
  if (card.id) {
    return `id:${card.id}`;
  }

  const heading =
    card.querySelector(
      ".panel-header h3",
    );

  const title =
    heading?.textContent
      ?.trim();

  if (title) {
    return `title:${title}`;
  }

  return `index:${index}`;
}

function captureWorkbenchUiState() {
  const inputs = {};

  for (const id of persistentInputIds) {
    const element =
      document.getElementById(id);

    if (!element) {
      continue;
    }

    if (
      element instanceof HTMLInputElement
      && element.type === "checkbox"
    ) {
      inputs[id] =
        element.checked;

      continue;
    }

    inputs[id] =
      element.value;
  }

  const collapsedPanels = [];

  Array.from(
    document.querySelectorAll(
      ".card",
    ),
  ).forEach(
    (card, index) => {
      if (
        !card.classList.contains(
          "panel-collapsed",
        )
      ) {
        return;
      }

      collapsedPanels.push(
        panelPersistenceKey(
          card,
          index,
        ),
      );
    },
  );

  try {
    window.localStorage.setItem(
      MERCATOR_UI_STATE_KEY,
      JSON.stringify({
        inputs,
        collapsedPanels,
      }),
    );
  } catch {
    // Persistence is optional. Do not break the workbench
    // if the browser blocks localStorage.
  }
}

function restoreWorkbenchUiState() {
  const state =
    readWorkbenchUiState();

  for (
    const [
      id,
      storedValue,
    ]
    of Object.entries(
      state.inputs,
    )
  ) {
    const element =
      document.getElementById(id);

    if (!element) {
      continue;
    }

    if (
      element instanceof HTMLInputElement
      && element.type === "checkbox"
    ) {
      element.checked =
        Boolean(storedValue);

      continue;
    }

    element.value =
      String(storedValue);
  }

  const collapsedSet =
    new Set(
      state.collapsedPanels,
    );

  Array.from(
    document.querySelectorAll(
      ".card",
    ),
  ).forEach(
    (card, index) => {
      const key =
        panelPersistenceKey(
          card,
          index,
        );

      setPanelCollapsed(
        card,
        collapsedSet.has(key),
      );
    },
  );
}

function initializeWorkbenchUiPersistence() {
  restoreWorkbenchUiState();

  for (const id of persistentInputIds) {
    const element =
      document.getElementById(id);

    if (!element) {
      continue;
    }

    const eventName =
      (
        element instanceof HTMLSelectElement
        || (
          element instanceof HTMLInputElement
          && element.type === "checkbox"
        )
      )
        ? "change"
        : "input";

    element.addEventListener(
      eventName,
      captureWorkbenchUiState,
    );
  }

  document.addEventListener(
    "click",
    (event) => {
      const target =
        event.target;

      if (
        !(target instanceof Element)
      ) {
        return;
      }

      if (
        target.closest(
          ".panel-collapse-button",
        )
        || target.closest(
          "#expandAllPanelsButton",
        )
        || target.closest(
          "#collapseAllPanelsButton",
        )
      ) {
        window.setTimeout(
          captureWorkbenchUiState,
          0,
        );
      }
    },
  );

  window.addEventListener(
    "beforeunload",
    captureWorkbenchUiState,
  );
}

function resetWorkbenchUiState() {
  try {
    window.localStorage.removeItem(
      MERCATOR_UI_STATE_KEY,
    );
  } catch {
    // Ignore localStorage failures.
  }

  window.location.reload();
}

initializeWorkbenchUiPersistence();



// ============================================================
// Workspace presets
// ============================================================

const WORKSPACE_PRESETS = {
  "core-credit": {
    instrumentIds:
      "1,2,3,4,5",

    values: {
      positionNotional: "1000000",
      portfolioRiskFaceValue: "1000000",
      riskDecompositionNotional: "1000000",
      hedgePositionNotional: "1000000",
      hedgeRatio: "1",
      includeCreditHedge: true,
      marketOverviewLimit: "100",
      marketOverviewQuality: "0.8",
    },
  },

  "rates-heavy": {
    instrumentIds:
      "1,2,3,4,5,6,7,8",

    values: {
      positionNotional: "1000000",
      stressPositionNotional: "1000000",
      stressTreasuryParallel: "25",
      stressTreasury2Y: "10",
      stressTreasury5Y: "20",
      stressTreasury10Y: "35",
      stressTreasury30Y: "50",
      stressCreditParallel: "0",
    },
  },

  "stress-basket": {
    instrumentIds:
      "1,2,3,4,5",

    values: {
      positionNotional: "1000000",
      stressPositionNotional: "1000000",
      stressTreasuryParallel: "50",
      stressTreasury2Y: "25",
      stressTreasury5Y: "40",
      stressTreasury10Y: "60",
      stressTreasury30Y: "75",
      stressCreditParallel: "100",
    },
  },

  "relative-value": {
    instrumentIds:
      "1,2,3,4,5,6,7,8,9,10",

    values: {
      relativeValueBucketWidth: "1.5",
      relativeValueMinimumPeers: "3",
      carryRollHorizon: "3",
      carryRollFinancingRate: "0.045",
      carryRollNormalization: "0.25",
      marketOverviewLimit: "100",
      marketOverviewQuality: "0.8",
    },
  },
};

function setWorkspaceControlValue(
  id,
  value,
) {
  const element =
    document.getElementById(id);

  if (!element) {
    return;
  }

  if (
    element instanceof HTMLInputElement
    && element.type === "checkbox"
  ) {
    element.checked =
      Boolean(value);

    return;
  }

  element.value =
    String(value);
}

function applyWorkspacePreset() {
  const select =
    document.getElementById(
      "workspacePresetSelect",
    );

  if (!select) {
    return;
  }

  const name =
    select.value;

  if (!name) {
    return;
  }

  const preset =
    WORKSPACE_PRESETS[name];

  if (!preset) {
    return;
  }

  const instrumentInput =
    document.getElementById(
      "instrumentIds",
    );

  if (
    instrumentInput
    && preset.instrumentIds
  ) {
    instrumentInput.value =
      preset.instrumentIds;
  }

  for (
    const [
      id,
      value,
    ]
    of Object.entries(
      preset.values || {},
    )
  ) {
    setWorkspaceControlValue(
      id,
      value,
    );
  }

  captureWorkbenchUiState();

  log(
    `Workspace preset applied: ${select.options[select.selectedIndex].text}`,
  );
}

function resetWorkspace() {
  const confirmed =
    window.confirm(
      "Reset saved workspace settings and reload defaults?",
    );

  if (!confirmed) {
    return;
  }

  resetWorkbenchUiState();
}

const applyWorkspacePresetButton =
  document.getElementById(
    "applyWorkspacePresetButton",
  );

if (applyWorkspacePresetButton) {
  applyWorkspacePresetButton.addEventListener(
    "click",
    applyWorkspacePreset,
  );
}

const resetWorkspaceButton =
  document.getElementById(
    "resetWorkspaceButton",
  );

if (resetWorkspaceButton) {
  resetWorkspaceButton.addEventListener(
    "click",
    resetWorkspace,
  );
}


// ============================================================
// Portfolio Suite
// ============================================================

async function runPortfolioSuite() {
  const button =
    document.getElementById(
      "runPortfolioSuiteButton",
    );

  if (button) {
    button.disabled = true;
    button.textContent =
      "Running Suite...";
  }

  try {
    const instrumentIds =
      parseInstrumentIds();

    if (instrumentIds.length < 1) {
      throw new Error(
        "Portfolio Suite requires at least one instrument ID.",
      );
    }

    const riskFaceValue =
      Number(
        document.getElementById(
          "portfolioRiskFaceValue",
        )?.value
        || 1000000,
      );

    const riskNotional =
      Number(
        document.getElementById(
          "riskDecompositionNotional",
        )?.value
        || 1000000,
      );

    const hedgeNotional =
      Number(
        document.getElementById(
          "hedgePositionNotional",
        )?.value
        || 1000000,
      );

    const hedgeRatio =
      Number(
        document.getElementById(
          "hedgeRatio",
        )?.value
        || 1,
      );

    const includeCreditHedge =
      Boolean(
        document.getElementById(
          "includeCreditHedge",
        )?.checked,
      );

    const portfolioRiskPayload =
      await request(
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
                    riskFaceValue,
                }),
              ),
          }),
        },
      );

    renderPortfolioRisk(
      portfolioRiskPayload,
    );

    const decompositionPayload =
      await request(
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
              riskNotional,
          }),
        },
      );

    renderRiskDecomposition(
      decompositionPayload,
    );

    let varPayload = null;

    try {
      await runHistoricalVar();

      const varElement =
        document.getElementById(
          "historicalVarValue",
        );

      if (varElement) {
        varPayload = {
          display:
            varElement.textContent,
        };
      }
    } catch (error) {
      log(
        `Portfolio Suite VaR step failed: ${error.message}`,
      );
    }

    const hedgePayload =
      await request(
        "/risk/hedge-recommendations",
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
              hedgeNotional,
            hedge_ratio:
              hedgeRatio,
            include_credit_hedge:
              includeCreditHedge,
          }),
        },
      );

    renderHedgeRecommendations(
      hedgePayload,
    );

    const marketValue =
      document.getElementById(
        "portfolioSuiteMarketValue",
      );

    const dv01 =
      document.getElementById(
        "portfolioSuiteDv01",
      );

    const cs01 =
      document.getElementById(
        "portfolioSuiteCs01",
      );

    const varValue =
      document.getElementById(
        "portfolioSuiteVar",
      );

    const residualDv01 =
      document.getElementById(
        "portfolioSuiteResidualDv01",
      );

    const residualCs01 =
      document.getElementById(
        "portfolioSuiteResidualCs01",
      );

    if (marketValue) {
      marketValue.textContent =
        currency(
          portfolioRiskPayload
            .total_market_value,
        );
    }

    if (dv01) {
      dv01.textContent =
        number(
          decompositionPayload
            .total_dv01,
          2,
        );
    }

    if (cs01) {
      cs01.textContent =
        number(
          decompositionPayload
            .total_cs01,
          2,
        );
    }

    if (varValue) {
      varValue.textContent =
        varPayload?.display
        || "See VaR panel";
    }

    if (residualDv01) {
      residualDv01.textContent =
        number(
          hedgePayload
            .residual_dv01,
          2,
        );
    }

    if (residualCs01) {
      residualCs01.textContent =
        number(
          hedgePayload
            .residual_cs01,
          2,
        );
    }

    log(
      `Portfolio Suite completed for ${instrumentIds.length} instruments.`,
    );
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent =
        "Run Portfolio Suite";
    }
  }
}

const runPortfolioSuiteButton =
  document.getElementById(
    "runPortfolioSuiteButton",
  );

if (runPortfolioSuiteButton) {
  runPortfolioSuiteButton.addEventListener(
    "click",
    () =>
      handleAction(
        runPortfolioSuite,
      ),
  );
}


// ============================================================
// Command Palette
// ============================================================

const commandPaletteCommands = [
  {
    title: "Market Overview",
    description:
      "Jump to the latest evaluated bond universe.",
    category: "Navigate",
    keywords:
      "market universe latest prices bonds",
    run() {
      document
        .getElementById(
          "market-overview",
        )
        ?.scrollIntoView({
          behavior: "smooth",
        });
    },
  },

  {
    title: "Price History",
    description:
      "Jump to instrument historical analytics.",
    category: "Navigate",
    keywords:
      "history price instrument chart",
    run() {
      document
        .getElementById(
          "history",
        )
        ?.scrollIntoView({
          behavior: "smooth",
        });
    },
  },

  {
    title: "Risk Management",
    description:
      "Jump to portfolio risk analytics.",
    category: "Navigate",
    keywords:
      "risk var stress hedge dv01 cs01",
    run() {
      document
        .getElementById(
          "risk",
        )
        ?.scrollIntoView({
          behavior: "smooth",
        });
    },
  },

  {
    title: "Replay & Stream",
    description:
      "Jump to market stream and replay operations.",
    category: "Navigate",
    keywords:
      "stream replay websocket operations",
    run() {
      document
        .getElementById(
          "operations",
        )
        ?.scrollIntoView({
          behavior: "smooth",
        });
    },
  },

  {
    title: "Load Market Overview",
    description:
      "Refresh summary and latest bond prices.",
    category: "Market",
    keywords:
      "load market summary latest",
    async run() {
      await handleAction(
        loadMarketOverview,
      );
    },
  },

  {
    title: "Run Portfolio Suite",
    description:
      "Run the consolidated portfolio risk workflow.",
    category: "Portfolio",
    keywords:
      "portfolio suite var hedge decomposition",
    async run() {
      await handleAction(
        runPortfolioSuite,
      );
    },
  },

  {
    title: "Calculate Portfolio Risk",
    description:
      "Calculate aggregate and position-level portfolio risk.",
    category: "Portfolio",
    keywords:
      "portfolio duration spread dv01 convexity",
    async run() {
      await handleAction(
        runPortfolioRisk,
      );
    },
  },

  {
    title: "Run Risk Decomposition",
    description:
      "Calculate DV01, CS01, and key-rate exposure.",
    category: "Risk",
    keywords:
      "decomposition key rate dv01 cs01",
    async run() {
      await handleAction(
        runRiskDecomposition,
      );
    },
  },

  {
    title: "Run Historical VaR",
    description:
      "Calculate historical portfolio Value at Risk.",
    category: "Risk",
    keywords:
      "historical var value at risk",
    async run() {
      await handleAction(
        runHistoricalVar,
      );
    },
  },

  {
    title: "Generate Hedge Recommendations",
    description:
      "Generate Treasury and credit hedge notionals.",
    category: "Risk",
    keywords:
      "hedge treasury credit residual",
    async run() {
      await handleAction(
        runHedgeRecommendations,
      );
    },
  },

  {
    title: "Run Stress Test",
    description:
      "Apply Treasury and credit stress shocks.",
    category: "Risk",
    keywords:
      "stress treasury credit pnl shock",
    async run() {
      await handleAction(
        runStressTest,
      );
    },
  },

  {
    title: "Run Relative Value Screen",
    description:
      "Rank bonds against duration-matched peers.",
    category: "Analytics",
    keywords:
      "relative value cheap rich z score",
    async run() {
      await handleAction(
        runRelativeValueScreen,
      );
    },
  },

  {
    title: "Rank Carry & Roll",
    description:
      "Rank expected carry, roll-down, and normalization.",
    category: "Analytics",
    keywords:
      "carry roll financing return",
    async run() {
      await handleAction(
        runCarryRoll,
      );
    },
  },

  {
    title: "Refresh Stream Status",
    description:
      "Retrieve the latest simulated stream state.",
    category: "Operations",
    keywords:
      "stream status sequence clients",
    async run() {
      await handleAction(
        refreshMarketStreamStatus,
      );
    },
  },

  {
    title: "Refresh System Health",
    description:
      "Refresh API, stream, and market status.",
    category: "Operations",
    keywords:
      "health api status system",
    async run() {
      await handleAction(
        refreshSystemHealth,
      );
    },
  },

  {
    title: "Expand All Panels",
    description:
      "Expand every analytical panel.",
    category: "Workspace",
    keywords:
      "expand panels workspace",
    run() {
      document
        .querySelectorAll(".card")
        .forEach((card) => {
          setPanelCollapsed(
            card,
            false,
          );
        });

      captureWorkbenchUiState();
    },
  },

  {
    title: "Collapse All Panels",
    description:
      "Collapse every analytical panel.",
    category: "Workspace",
    keywords:
      "collapse panels workspace",
    run() {
      document
        .querySelectorAll(".card")
        .forEach((card) => {
          setPanelCollapsed(
            card,
            true,
          );
        });

      captureWorkbenchUiState();
    },
  },
];

let commandPaletteSelection = 0;

function commandPaletteElements() {
  return {
    overlay:
      document.getElementById(
        "commandPalette",
      ),

    input:
      document.getElementById(
        "commandPaletteInput",
      ),

    results:
      document.getElementById(
        "commandPaletteResults",
      ),
  };
}

function filteredCommandPaletteCommands() {
  const {
    input,
  } = commandPaletteElements();

  const query =
    String(
      input?.value || "",
    )
      .trim()
      .toLowerCase();

  if (!query) {
    return commandPaletteCommands;
  }

  return commandPaletteCommands.filter(
    (command) => {
      const haystack = [
        command.title,
        command.description,
        command.category,
        command.keywords,
      ]
        .join(" ")
        .toLowerCase();

      return haystack.includes(
        query,
      );
    },
  );
}

function renderCommandPalette() {
  const {
    results,
  } = commandPaletteElements();

  if (!results) {
    return;
  }

  const commands =
    filteredCommandPaletteCommands();

  if (
    commandPaletteSelection
    >= commands.length
  ) {
    commandPaletteSelection = 0;
  }

  if (commands.length === 0) {
    results.innerHTML = `
      <div class="command-palette-empty">
        No matching commands.
      </div>
    `;

    return;
  }

  results.innerHTML =
    commands
      .map(
        (command, index) => `
          <button
            type="button"
            class="
              command-palette-item
              ${
                index
                  === commandPaletteSelection
                  ? "selected"
                  : ""
              }
            "
            data-command-index="${index}"
          >
            <span
              class="command-palette-item-main"
            >
              <span
                class="command-palette-item-title"
              >
                ${command.title}
              </span>

              <span
                class="command-palette-item-description"
              >
                ${command.description}
              </span>
            </span>

            <span
              class="command-palette-item-category"
            >
              ${command.category}
            </span>
          </button>
        `,
      )
      .join("");
}

function openCommandPalette() {
  const {
    overlay,
    input,
  } = commandPaletteElements();

  if (!overlay || !input) {
    return;
  }

  commandPaletteSelection = 0;

  overlay.hidden = false;

  document.body.classList.add(
    "command-palette-open",
  );

  input.value = "";

  renderCommandPalette();

  window.setTimeout(
    () => input.focus(),
    0,
  );
}

function closeCommandPalette() {
  const {
    overlay,
  } = commandPaletteElements();

  if (!overlay) {
    return;
  }

  overlay.hidden = true;

  document.body.classList.remove(
    "command-palette-open",
  );
}

async function executeCommandPaletteSelection() {
  const commands =
    filteredCommandPaletteCommands();

  const command =
    commands[
      commandPaletteSelection
    ];

  if (!command) {
    return;
  }

  closeCommandPalette();

  await command.run();
}

function initializeCommandPalette() {
  const {
    overlay,
    input,
    results,
  } = commandPaletteElements();

  if (
    !overlay
    || !input
    || !results
  ) {
    return;
  }

  document.addEventListener(
    "keydown",
    async (event) => {
      if (
        (
          event.metaKey
          || event.ctrlKey
        )
        && event.key.toLowerCase() === "k"
      ) {
        event.preventDefault();

        if (overlay.hidden) {
          openCommandPalette();
        } else {
          closeCommandPalette();
        }

        return;
      }

      if (overlay.hidden) {
        return;
      }

      if (event.key === "Escape") {
        event.preventDefault();
        closeCommandPalette();
        return;
      }

      const commands =
        filteredCommandPaletteCommands();

      if (event.key === "ArrowDown") {
        event.preventDefault();

        commandPaletteSelection =
          commands.length === 0
            ? 0
            : (
                commandPaletteSelection
                + 1
              ) % commands.length;

        renderCommandPalette();
        return;
      }

      if (event.key === "ArrowUp") {
        event.preventDefault();

        commandPaletteSelection =
          commands.length === 0
            ? 0
            : (
                commandPaletteSelection
                - 1
                + commands.length
              ) % commands.length;

        renderCommandPalette();
        return;
      }

      if (event.key === "Enter") {
        event.preventDefault();

        await executeCommandPaletteSelection();
      }
    },
  );

  input.addEventListener(
    "input",
    () => {
      commandPaletteSelection = 0;
      renderCommandPalette();
    },
  );

  results.addEventListener(
    "click",
    async (event) => {
      const target =
        event.target;

      if (
        !(target instanceof Element)
      ) {
        return;
      }

      const item =
        target.closest(
          "[data-command-index]",
        );

      if (!item) {
        return;
      }

      commandPaletteSelection =
        Number(
          item.getAttribute(
            "data-command-index",
          ),
        );

      await executeCommandPaletteSelection();
    },
  );

  overlay.addEventListener(
    "click",
    (event) => {
      if (
        event.target === overlay
      ) {
        closeCommandPalette();
      }
    },
  );

  renderCommandPalette();
}

initializeCommandPalette();


// ============================================================
// Toast smoke-test helper
// ============================================================

window.mercatorToastTest = function () {
  toastSuccess(
    "Portfolio analytics completed successfully.",
    "Test success",
  );

  window.setTimeout(
    () => {
      toastWarning(
        "Market data may be stale.",
        "Test warning",
      );
    },
    400,
  );

  window.setTimeout(
    () => {
      toastError(
        "Example API failure.",
        "Test error",
      );
    },
    800,
  );
};
