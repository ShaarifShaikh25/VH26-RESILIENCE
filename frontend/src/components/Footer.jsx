import { motion } from 'framer-motion'
import styles from './Footer.module.css'

export default function Footer() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <motion.footer
      className={styles.footer}
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className={styles.container}>
        {/* Main top grid */}
        <div className={styles.topGrid}>
          {/* Brand & mission column */}
          <div className={styles.brandCol}>
            <div className={styles.brandTitle}>RESILIENCE</div>
            <p className={styles.brandDesc}>
              Adaptive, Application-aware Cache Management System engineered to eliminate bottlenecks,
              unify memory nodes, and coordinate critical signals with zero-loss efficiency.
            </p>
            <div className={styles.systemStatusBadge}>
              <span className={styles.statusPulse} />
              <span className={styles.statusText}>ALL SYSTEMS OPERATIONAL</span>
            </div>
          </div>

          {/* Links columns */}
          <div className={styles.linksGrid}>
              <div className={styles.col}>
                <div className={styles.colHeader}>SYSTEM</div>
                <ul className={styles.colList}>
                  <li><a href="#system">Architecture</a></li>
                  <li><a href="/docs" target="_blank" rel="noopener noreferrer">FastAPI Swagger Docs</a></li>
                  <li><a href="/metrics" target="_blank" rel="noopener noreferrer">Live Metrics API</a></li>
                  <li><a href="#network">Telemetry Core</a></li>
                </ul>
              </div>

            <div className={styles.col}>
              <div className={styles.colHeader}>NETWORK</div>
              <ul className={styles.colList}>
                <li><a href="#network">Team Roster</a></li>
                <li><a href="#network">Frame Telemetry</a></li>
                <li><a href="#network">Cluster Health</a></li>
                <li><a href="#network">Protocol Specs</a></li>
              </ul>
            </div>

            <div className={styles.col}>
              <div className={styles.colHeader}>EVENT</div>
              <ul className={styles.colList}>
                <li><span className={styles.plainLink}>VCET Hackathon 2026</span></li>
                <li><span className={styles.plainLink}>Team Resilience</span></li>
                <li><span className={styles.plainLink}>React Three Fiber</span></li>
                <li><span className={styles.plainLink}>Build v2.4.0</span></li>
              </ul>
            </div>
          </div>
        </div>

        {/* Live telemetry bar */}
        <div className={styles.telemetryBar}>
          <div className={styles.telemetryGroup}>
            <div className={styles.telemetryItem}>
              <span className={styles.telemetryKey}>CLUSTER</span>
              <span className={styles.telemetryVal}>RES-PROD-01</span>
            </div>
            <div className={styles.telemetryItem}>
              <span className={styles.telemetryKey}>LATENCY</span>
              <span className={styles.telemetryVal}>&lt; 2ms</span>
            </div>
            <div className={styles.telemetryItem}>
              <span className={styles.telemetryKey}>UPTIME</span>
              <span className={styles.telemetryVal}>99.98%</span>
            </div>
            <div className={styles.telemetryItem}>
              <span className={styles.telemetryKey}>NODES</span>
              <span className={styles.telemetryVal}>04 ACTIVE</span>
            </div>
          </div>

          <button onClick={scrollToTop} className={styles.backToTop} aria-label="Back to top">
            <span>BACK TO TOP</span>
            <span className={styles.topArrow}>↑</span>
          </button>
        </div>

        {/* Divider */}
        <div className={styles.divider} />

        {/* Bottom copyright & attribution row */}
        <div className={styles.bottomRow}>
          <div className={styles.copyright}>
            © 2026 TEAM RESILIENCE • VCET HACKATHON. ALL RIGHTS RESERVED.
          </div>
          <div className={styles.quote}>
            "Turning fragmented signals into coordinated action when every second matters."
          </div>
        </div>
      </div>
    </motion.footer>
  )
}
