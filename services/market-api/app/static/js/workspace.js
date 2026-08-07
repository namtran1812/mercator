let manualWorkspaceNavigation = false;
let manualWorkspaceTimer = null;


function findWorkspaceHeading(
  title,
) {
  const normalizedTitle =
    title
      .trim()
      .toLowerCase();

  return Array
    .from(
      document.querySelectorAll(
        "h2",
      ),
    )
    .find(
      (heading) =>
        heading.textContent
          .trim()
          .toLowerCase()
        === normalizedTitle,
    );
}


function setWorkspaceContext(
  title,
) {
  const context =
    document.getElementById(
      "workspaceContextTitle",
    );

  if (!context) {
    return;
  }

  context.textContent =
    title;
}


function activateWorkspaceNav(
  button,
) {
  document
    .querySelectorAll(
      ".research-nav-item",
    )
    .forEach(
      (item) => {
        item.classList.remove(
          "active",
        );
      },
    );

  button.classList.add(
    "active",
  );
}


function beginManualWorkspaceNavigation() {
  manualWorkspaceNavigation =
    true;

  if (manualWorkspaceTimer) {
    clearTimeout(
      manualWorkspaceTimer,
    );
  }

  manualWorkspaceTimer =
    setTimeout(
      () => {
        manualWorkspaceNavigation =
          false;

        manualWorkspaceTimer =
          null;
      },
      900,
    );
}


function initializeResearchWorkspace() {
  const items =
    Array.from(
      document.querySelectorAll(
        "[data-workspace-heading]",
      ),
    );


  if (!items.length) {
    return;
  }


  const observed = [];


  /*
   * Resolve every sidebar button to its
   * corresponding section once.
   */
  items.forEach(
    (item) => {
      const title =
        item.dataset
          .workspaceHeading;

      const heading =
        findWorkspaceHeading(
          title,
        );

      if (!heading) {
        console.warn(
          "Mercator workspace heading not found:",
          title,
        );

        return;
      }


      /*
       * The section-title container is the
       * navigation anchor rather than the H2
       * itself.
       */
      const section =
        heading.closest(
          ".section-title",
        )
        || heading.parentElement
        || heading;


      observed.push(
        {
          button: item,
          title,
          element: section,
        },
      );


      /*
       * Manual sidebar navigation.
       */
      item.addEventListener(
        "click",
        () => {
          beginManualWorkspaceNavigation();

          activateWorkspaceNav(
            item,
          );

          setWorkspaceContext(
            title,
          );

          section.scrollIntoView(
            {
              behavior: "smooth",
              block: "start",
            },
          );
        },
      );
    },
  );


  /*
   * Scroll-based navigation.
   *
   * Important:
   * do not override the sidebar while a
   * manual smooth-scroll is in progress.
   */
  const observer =
    new IntersectionObserver(
      (entries) => {
        if (
          manualWorkspaceNavigation
        ) {
          return;
        }

        const visible =
          entries
            .filter(
              (entry) =>
                entry.isIntersecting,
            )
            .sort(
              (a, b) =>
                b.intersectionRatio
                - a.intersectionRatio,
            );


        if (!visible.length) {
          return;
        }


        const target =
          visible[0].target;


        const match =
          observed.find(
            (item) =>
              item.element
              === target,
          );


        if (!match) {
          return;
        }


        activateWorkspaceNav(
          match.button,
        );

        setWorkspaceContext(
          match.title,
        );
      },

      {
        root: null,

        rootMargin:
          "-15% 0px -70% 0px",

        threshold: [
          0,
          0.05,
          0.15,
          0.3,
        ],
      },
    );


  observed.forEach(
    (item) => {
      observer.observe(
        item.element,
      );
    },
  );


  /*
   * Start on the first valid workspace.
   */
  if (observed.length) {
    const first =
      observed[0];

    activateWorkspaceNav(
      first.button,
    );

    setWorkspaceContext(
      first.title,
    );
  }
}


if (
  document.readyState
  === "loading"
) {
  document.addEventListener(
    "DOMContentLoaded",
    initializeResearchWorkspace,
  );
}

else {
  initializeResearchWorkspace();
}
