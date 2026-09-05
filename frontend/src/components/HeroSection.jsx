import { useRef } from 'react'
import { motion, useMotionValue, useTransform, useSpring } from 'framer-motion'
import RobotScene from './RobotScene'
import TechGrid from './TechGrid'
import { useMouseRef } from '../hooks/useMouseRef'
import styles from './HeroSection.module.css'

export default function HeroSection() {
  const mouseRef = useMouseRef()

  // Framer-motion values for RESILIENCE text parallax
  // We sample mouse position from the ref at pointer events via framer
  const motionX = useMotionValue(0)
  const motionY = useMotionValue(0)

  const springX = useSpring(motionX, { stiffness: 40, damping: 20 })
  const springY = useSpring(motionY, { stiffness: 40, damping: 20 })

  const textX = useTransform(springX, [-1, 1], [-18, 18])
  const textY = useTransform(springY, [-1, 1], [6, -6])

  const subtitleX = useTransform(springX, [-1, 1], [-8, 8])

  const handlePointerMove = (e) => {
    const nx = (e.clientX / window.innerWidth) * 2 - 1
    const ny = -((e.clientY / window.innerHeight) * 2 - 1)
    motionX.set(nx)
    motionY.set(ny)
  }

  return (
    <section
      id="system"
      className={styles.hero}
      onPointerMove={handlePointerMove}
    >
      <TechGrid />

      {/* RESILIENCE backdrop text */}
      <motion.div
        className={styles.backdropText}
        style={{ x: textX, y: textY, translateX: '-50%', translateY: '-50%' }}
        initial={{ opacity: 0, scale: 0.92, letterSpacing: '0.24em' }}
        animate={{ opacity: 1, scale: 1, letterSpacing: '0.18em' }}
        transition={{ duration: 1.4, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
      >
        RESILIENCE
      </motion.div>

      {/* 3D Robot — fills the section */}
      <RobotScene mouseRef={mouseRef} />

      {/* Hero content overlay */}
      <div className={styles.content}>
        <motion.h1
          className={styles.title}
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.35, ease: [0.22, 1, 0.36, 1] }}
        >
          Adaptive, Application-aware
          <br />
          Cache Management System
        </motion.h1>

        <motion.p
          className={styles.description}
          style={{ x: subtitleX }}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.95, delay: 0.55, ease: [0.22, 1, 0.36, 1] }}
        >
          Turning fragmented signals into coordinated action
          <br />
          when every second matters.
        </motion.p>

        <motion.div
          className={styles.ctas}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.75, ease: [0.22, 1, 0.36, 1] }}
        >
          <motion.a
            href="#network"
            className={styles.btnPrimary}
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 400, damping: 20 }}
          >
            EXPLORE SYSTEM
          </motion.a>
          <motion.a
            href="#network"
            className={styles.btnSecondary}
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 400, damping: 20 }}
          >
            VIEW NETWORK
          </motion.a>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className={styles.scrollIndicator}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.95, ease: [0.22, 1, 0.36, 1] }}
      >
        <motion.div
          className={styles.scrollLine}
          animate={{ scaleY: [0.6, 1.2, 0.6], opacity: [0.35, 0.85, 0.35] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        />
        <span className={styles.scrollLabel}>SCROLL</span>
      </motion.div>
    </section>
  )
}
