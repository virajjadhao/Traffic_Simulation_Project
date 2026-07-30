import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MainContent } from './MainContent';
import styles from './MainLayout.module.css';

export function MainLayout() {
  return (
    <div className={styles.shell}>
      <Header />
      <div className={styles.body}>
        <Sidebar />
        <MainContent />
      </div>
    </div>
  );
}
