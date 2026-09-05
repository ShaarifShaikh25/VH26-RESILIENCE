import { motion } from 'framer-motion'
import styles from './NetworkSection.module.css'

/* ── Team data ── */
const TEAM = [
  {
    id: 1,
    name: 'Muddassir\nMushtaque Sayyed',
    role: 'DATA INTELLIGENCE',
    initial: 'M',
    image: '/muddassir.png',
    imagePosition: 'center 20%',
    frame: '01',
  },
  {
    id: 2,
    name: 'Hasnain Shaikh\nQayyum Khatik',
    role: 'AI SYSTEMS',
    initial: 'H',
    image: '/hasnain.jpg',
    imagePosition: 'center 25%',
    frame: '02',
  },
  {
    id: 3,
    name: 'Huzefa Siddique\nBagwan',
    role: 'NETWORK OPS',
    initial: 'HZ',
    image: '/huzefa.png',
    imagePosition: 'center 52%',
    frame: '03',
  },
  {
    id: 4,
    name: 'Shaikh Mohammad\nShaarif M. Raees',
    role: 'LEAD ARCHITECT',
    initial: 'S',
    image: '/shaarif.png',
    imagePosition: 'center 22%',
    frame: '04',
  },
]

export default function NetworkSection() {
  return (
    <section id="network" className={styles.section}>
      {/* ── Top header row ── */}
      <div className={styles.topRow}>
        <motion.div
          className={styles.builtBy}
          initial={{ opacity: 0, y: -12 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          viewport={{ once: true }}
        >
          <span className={styles.builtByDot} />
          BUILD BY
        </motion.div>
      </div>

      {/* ── 4 Member Frames ── */}
      <div className={styles.framesGrid}>
        {TEAM.map((member, i) => (
          <motion.div
            key={member.id}
            className={styles.frame}
            initial={{ opacity: 0, y: 28 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] }}
            viewport={{ once: true }}
            whileHover={{ borderColor: 'rgba(239,68,68,0.4)', y: -4 }}
          >
            {/* Frame number */}
            <div className={styles.frameNumber}>FRAME {member.frame}</div>

            {/* Avatar area */}
            <div className={styles.avatar}>
              {member.image ? (
                <img
                  src={member.image}
                  alt={member.name.replace('\n', ' ')}
                  className={styles.avatarImg}
                  style={member.imagePosition ? { objectPosition: member.imagePosition } : undefined}
                />
              ) : (
                <span className={styles.avatarInitial}>{member.initial}</span>
              )}
              {/* Animated scan line */}
              <div className={styles.scanLine} />
            </div>

            {/* Member info */}
            <div className={styles.memberInfo}>
              {member.name.split('\n').map((line, j) => (
                <span key={j} className={j === 0 ? styles.memberName : styles.memberNameSub}>
                  {line}
                </span>
              ))}
              <span className={styles.memberRole}>{member.role}</span>
            </div>

            {/* Status indicator */}
            <div className={styles.frameStatus}>
              <span className={styles.statusDot} />
              <span className={styles.statusText}>ACTIVE</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* ── RESILIENCE big title ── */}
      <motion.div
        className={styles.resilienceTitle}
        initial={{ opacity: 0, y: 35, scale: 0.98 }}
        whileInView={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.9, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
        viewport={{ once: true }}
      >
        RESILIENCE
      </motion.div>

      {/* ── Stats row ── */}
      <div className={styles.statsRow}>
        {[
          { label: 'TEAM MEMBERS', value: '04' },
          { label: 'SYSTEM NODES', value: '24' },
          { label: 'RESPONSE TIME', value: '<2s' },
          { label: 'UPTIME',        value: '99.9%' },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            className={styles.stat}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 + i * 0.08, ease: [0.22, 1, 0.36, 1] }}
            viewport={{ once: true }}
          >
            <span className={styles.statValue}>{s.value}</span>
            <span className={styles.statLabel}>{s.label}</span>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
