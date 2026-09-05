import styles from './SystemIndicators.module.css'
import { motion } from 'framer-motion'

const indicators = [
  { label: 'SYSTEM STATUS',    value: 'OPERATIONAL', x: 'left',  y: 'top',    delay: 0.8  },
  { label: 'RESPONSE NETWORK', value: 'CONNECTED',   x: 'right', y: 'top',    delay: 1.0  },
  { label: 'AI CORE',          value: 'ACTIVE',      x: 'left',  y: 'bottom', delay: 1.15 },
  { label: 'THREAT MONITOR',   value: 'READY',       x: 'right', y: 'bottom', delay: 1.3  },
]

export default function SystemIndicators() {
  return (
    <>
      {indicators.map((ind) => (
        <motion.div
          key={ind.label}
          className={`${styles.indicator} ${styles[ind.x]} ${styles[ind.y]}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: ind.delay }}
        >
          <span className={styles.label}>{ind.label}</span>
          <span className={styles.value}>
            <span className={styles.dot} />
            {ind.value}
          </span>
        </motion.div>
      ))}
    </>
  )
}
