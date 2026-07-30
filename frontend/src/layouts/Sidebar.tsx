import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { id: 'home', label: 'Home', icon: '⌂' },
  { id: 'config', label: 'Configuration', icon: '⚙' },
  { id: 'simulation', label: 'Simulation', icon: '▶' },
  { id: 'comparison', label: 'Comparison', icon: '⇄' },
  { id: 'results', label: 'Results', icon: '☰' },
] as const;

export function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <nav className={styles.nav} aria-label="Main navigation">
        <ul className={styles.navList}>
          {NAV_ITEMS.map((item, index) => (
            <li key={item.id}>
              <button
                type="button"
                className={`${styles.navItem} ${index === 0 ? styles.navItemActive : ''}`}
                aria-current={index === 0 ? 'page' : undefined}
              >
                <span className={styles.navIcon} aria-hidden="true">
                  {item.icon}
                </span>
                <span className={styles.navLabel}>{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
