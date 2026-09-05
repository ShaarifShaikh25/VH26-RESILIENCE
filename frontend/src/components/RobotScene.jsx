import { Canvas } from '@react-three/fiber'
import { Environment, ContactShadows, BakeShadows } from '@react-three/drei'
import { Suspense } from 'react'
import { motion } from 'framer-motion'
import Robot from './Robot'
import styles from './RobotScene.module.css'

export default function RobotScene({ mouseRef }) {
  return (
    <motion.div
      className={styles.canvasWrapper}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 1.5, ease: [0.22, 1, 0.36, 1], delay: 0.1 }}
    >
      <Canvas
        camera={{ position: [0, 0.35, 5.2], fov: 40 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true, toneMapping: 3, toneMappingExposure: 1.1 }}
        style={{ background: 'transparent' }}
        shadows
      >
        <Suspense fallback={null}>
          {/* Very dim ambient so black robot stays mostly dark */}
          <ambientLight intensity={0.08} />

          {/* KEY LIGHT — top-left, cool-white, primary highlight */}
          <directionalLight
            position={[-4, 6, 3]}
            intensity={5}
            color="#d0d8f0"
            castShadow
            shadow-mapSize={[2048, 2048]}
            shadow-camera-near={0.1}
            shadow-camera-far={20}
          />

          {/* RIM LIGHT — top-right behind — creates chrome edge shimmer */}
          <directionalLight
            position={[5, 5, -5]}
            intensity={3}
            color="#ffffff"
          />

          {/* FILL — opposite side, very soft */}
          <directionalLight
            position={[3, -1, 4]}
            intensity={0.4}
            color="#98a0b8"
          />

          {/* BOTTOM BOUNCE — faint upward fill */}
          <directionalLight
            position={[0, -4, 2]}
            intensity={0.2}
            color="#ffffff"
          />

          {/* RED accent light — simulating chest glow spill */}
          <pointLight
            position={[0, 0.4, 2.2]}
            intensity={0.8}
            color="#ef4444"
            distance={5}
            decay={2}
          />

          {/* Eye glow lights */}
          <pointLight
            position={[-0.25, 1.55, 2.5]}
            intensity={0.4}
            color="#ffffff"
            distance={2}
          />
          <pointLight
            position={[0.25, 1.55, 2.5]}
            intensity={0.4}
            color="#ffffff"
            distance={2}
          />

          <Robot mouseRef={mouseRef} />

          <ContactShadows
            position={[0, -2.85, 0]}
            opacity={0.55}
            scale={8}
            blur={4}
            far={5}
            color="#000000"
          />

          <Environment preset="city" />
        </Suspense>
      </Canvas>
    </motion.div>
  )
}
