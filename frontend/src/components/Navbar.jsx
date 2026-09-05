import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import styles from './Navbar.module.css'

const links = [
  { label: 'SYSTEM', href: '#system' },
  { label: 'NETWORK', href: '#network' },
  { label: 'API DOCS', href: '/docs' },
]
const STREAMLIT_URL = import.meta.env.VITE_STREAMLIT_URL || 'http://192.168.20.127:8501'

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <motion.nav
      className={styles.nav}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className={styles.inner}>
        {/* Logo */}
        <motion.a
          href="#"
          className={styles.logo}
          initial={{ opacity: 0, x: -18 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
        >
          RESILIENCE
        </motion.a>

        {/* Desktop links */}
        <ul className={styles.links}>
          {links.map((l, i) => (
            <motion.li
              key={l.label}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.25 + i * 0.08, ease: [0.22, 1, 0.36, 1] }}
            >
              <a href={l.href} className={styles.link} target={l.href.startsWith('http') || l.href.startsWith('/docs') ? '_blank' : undefined} rel={l.href.startsWith('/docs') ? 'noopener noreferrer' : undefined}>
                {l.label}
              </a>
            </motion.li>
          ))}
        </ul>

        {/* Dashboard CTA */}
        <motion.a
          href={STREAMLIT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.dashboardBtn}
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.45, ease: [0.22, 1, 0.36, 1] }}
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.97 }}
        >
          <span className={styles.dashboardArrow}>→</span>
          DASHBOARD
        </motion.a>

        {/* Mobile hamburger */}
        <button
          className={styles.hamburger}
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          <span className={open ? styles.barOpen : styles.bar} />
          <span className={open ? styles.barHide : styles.bar} />
          <span className={open ? styles.barOpen2 : styles.bar} />
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            className={styles.mobileMenu}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            {links.map((l) => (
              <a
                key={l.label}
                href={l.href}
                className={styles.mobileLink}
                target={l.href.startsWith('http') || l.href.startsWith('/docs') ? '_blank' : undefined}
                rel={l.href.startsWith('/docs') ? 'noopener noreferrer' : undefined}
                onClick={() => setOpen(false)}
              >
                {l.label}
              </a>
            ))}
            <a
              href={STREAMLIT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.mobileDashboardLink}
              onClick={() => setOpen(false)}
            >
              → OPEN STREAMLIT DASHBOARD
            </a>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  )
}
