import styles from './Header.module.css';

export function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.logo} aria-hidden="true">
          ◈
        </span>
        <div className={styles.titles}>
          <h1 className={styles.title}>Traffic Intersection Control Comparison</h1>
          <p className={styles.subtitle}>Fixed-Time Signal vs. Roundabout Simulation</p>
        </div>
      </div>
      <div className={styles.status} aria-label="Connection status">
        <span className={styles.statusDot} aria-hidden="true" />
        <span className={styles.statusLabel}>Disconnected</span>
      </div>
    </header>
  );
}
