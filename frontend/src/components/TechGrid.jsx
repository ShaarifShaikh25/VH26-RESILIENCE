import { motion } from 'framer-motion'
import styles from './TechGrid.module.css'

export default function TechGrid() {
  return (
    <motion.div
      className={styles.grid}
      aria-hidden="true"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.5, ease: 'easeOut' }}
    >
      <svg
        className={styles.svg}
        xmlns="http://www.w3.org/2000/svg"
        width="100%"
        height="100%"
      >
        <defs>
          <pattern
            id="techGridLight"
            x="0"
            y="0"
            width="56"
            height="56"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 56 0 L 0 0 0 56"
              fill="none"
              stroke="rgba(0, 0, 0, 0.045)"
              strokeWidth="0.8"
            />
          </pattern>

          {/* Fade mask — center clear, fades subtly at bounds */}
          <radialGradient id="lightGridFade" cx="50%" cy="50%" r="60%">
            <stop offset="0%"   stopColor="white" stopOpacity="1" />
            <stop offset="70%"  stopColor="white" stopOpacity="0.6" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
          <mask id="lightGridMask">
            <rect width="100%" height="100%" fill="url(#lightGridFade)" />
          </mask>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="url(#techGridLight)"
          mask="url(#lightGridMask)"
        />

        {/* Subtle center cross marker */}
        <line x1="50%" y1="46%" x2="50%" y2="54%" stroke="rgba(220, 38, 38, 0.25)" strokeWidth="1" />
        <line x1="46%" y1="50%" x2="54%" y2="50%" stroke="rgba(220, 38, 38, 0.25)" strokeWidth="1" />
        <circle cx="50%" cy="50%" r="3.5" fill="none" stroke="rgba(220, 38, 38, 0.3)" strokeWidth="0.8" />
      </svg>
    </motion.div>
  )
}
