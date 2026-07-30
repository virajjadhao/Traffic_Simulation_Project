import styles from './MainContent.module.css';

export function MainContent() {
  return (
    <main className={styles.main}>
      <section className={styles.welcome} aria-labelledby="welcome-heading">
        <h2 id="welcome-heading">Dashboard</h2>
        <p className={styles.welcomeText}>
          Simulation visualization and metrics will appear here in upcoming phases.
        </p>
      </section>

      <div className={styles.grid}>
        <section
          className={styles.panel}
          aria-labelledby="viewport-heading"
        >
          <header className={styles.panelHeader}>
            <h3 id="viewport-heading">Simulation Viewport</h3>
            <span className={styles.panelBadge}>Canvas</span>
          </header>
          <div className={styles.viewportPlaceholder}>
            <div className={styles.viewportInner}>
              <span className={styles.viewportIcon} aria-hidden="true">
                ◈
              </span>
              <p className={styles.placeholderText}>
                HTML5 Canvas rendering area
              </p>
              <p className={styles.placeholderHint}>
                Intersection visualization · ISSUE-043+
              </p>
            </div>
          </div>
        </section>

        <aside className={styles.sidePanels}>
          <section
            className={styles.panel}
            aria-labelledby="metrics-heading"
          >
            <header className={styles.panelHeader}>
              <h3 id="metrics-heading">Metrics</h3>
              <span className={styles.panelBadge}>Live</span>
            </header>
            <div className={styles.metricsPlaceholder}>
              <ul className={styles.metricStubs}>
                <li className={styles.metricStub}>
                  <span className={styles.metricLabel}>Throughput</span>
                  <span className={styles.metricValue}>—</span>
                </li>
                <li className={styles.metricStub}>
                  <span className={styles.metricLabel}>Avg Wait Time</span>
                  <span className={styles.metricValue}>—</span>
                </li>
                <li className={styles.metricStub}>
                  <span className={styles.metricLabel}>Queue Length</span>
                  <span className={styles.metricValue}>—</span>
                </li>
              </ul>
            </div>
          </section>

          <section
            className={styles.panel}
            aria-labelledby="controls-heading"
          >
            <header className={styles.panelHeader}>
              <h3 id="controls-heading">Controls</h3>
            </header>
            <div className={styles.controlsPlaceholder}>
              <div className={styles.controlRow}>
                <button type="button" className={styles.controlButton} disabled>
                  Start
                </button>
                <button type="button" className={styles.controlButton} disabled>
                  Pause
                </button>
                <button type="button" className={styles.controlButton} disabled>
                  Stop
                </button>
              </div>
              <p className={styles.placeholderHint}>
                Playback controls · ISSUE-042+
              </p>
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}
