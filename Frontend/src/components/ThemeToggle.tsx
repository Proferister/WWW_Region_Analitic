import styles from './ThemeToggle.module.css'

interface ThemeToggleProps {
  isDark: boolean
  onToggle: () => void
}

const ThemeToggle = ({ isDark, onToggle }: ThemeToggleProps) => (
  <button
    className={`${styles.toggle} ${isDark ? styles.dark : styles.light}`}
    onClick={onToggle}
    aria-label="Toggle theme"
  >
    <span className={styles.knob}>
      {isDark ? '🌙' : '☀️'}
    </span>
  </button>
)

export default ThemeToggle
