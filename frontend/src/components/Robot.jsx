import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const DEG2RAD = Math.PI / 180
const HEAD_YAW_MAX   = 22 * DEG2RAD
const HEAD_PITCH_MAX = 14 * DEG2RAD
const TORSO_YAW_MAX  =  4 * DEG2RAD
const HEAD_LERP   = 0.04
const TORSO_LERP  = 0.02

function lerp(a, b, t) { return a + (b - a) * t }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }

/* ─── SHARED MATERIALS ────────────────────────────────────────────────────── */
function useMat() {
  return useMemo(() => {
    const glossy = new THREE.MeshPhysicalMaterial({
      color: 0x060606,
      metalness: 0.95,
      roughness: 0.05,
      reflectivity: 1,
      clearcoat: 1,
      clearcoatRoughness: 0.05,
      envMapIntensity: 2,
    })
    const mid = new THREE.MeshPhysicalMaterial({
      color: 0x0e0e0e,
      metalness: 0.85,
      roughness: 0.18,
      clearcoat: 0.3,
    })
    const panel = new THREE.MeshStandardMaterial({
      color: 0x181818,
      metalness: 0.7,
      roughness: 0.45,
    })
    const dark = new THREE.MeshStandardMaterial({
      color: 0x080808,
      metalness: 0.6,
      roughness: 0.8,
    })
    const eye = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0xffffff,
      emissiveIntensity: 4,
      roughness: 0,
      metalness: 0,
    })
    const redAccent = new THREE.MeshStandardMaterial({
      color: 0xef4444,
      emissive: 0xef4444,
      emissiveIntensity: 1.2,
      roughness: 0.3,
    })
    const dimLine = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      metalness: 0.4,
      roughness: 0.7,
    })
    const chrome = new THREE.MeshPhysicalMaterial({
      color: 0x888888,
      metalness: 1,
      roughness: 0.02,
      reflectivity: 1,
    })
    return { glossy, mid, panel, dark, eye, redAccent, dimLine, chrome }
  }, [])
}

/* ─── HEAD ─────────────────────────────────────────────────────────────────── */
function Head({ mat }) {
  return (
    <group>
      {/* Core skull — slightly wider than tall */}
      <mesh material={mat.glossy} castShadow scale={[1, 0.9, 0.95]}>
        <sphereGeometry args={[0.7, 64, 48]} />
      </mesh>

      {/* Top crown plate */}
      <mesh position={[0, 0.52, 0]} material={mat.panel}>
        <cylinderGeometry args={[0.32, 0.55, 0.12, 32]} />
      </mesh>

      {/* Crown ridge ring */}
      <mesh position={[0, 0.58, 0]} material={mat.chrome}>
        <torusGeometry args={[0.32, 0.015, 12, 64]} />
      </mesh>

      {/* FACE VISOR — dark recessed area */}
      <mesh position={[0, 0.04, 0.54]} material={mat.dark} scale={[1, 0.85, 1]}>
        <sphereGeometry args={[0.52, 48, 32, 0, Math.PI * 2, 0, Math.PI * 0.52]} />
      </mesh>

      {/* Visor frame ring */}
      <mesh position={[0, 0.05, 0.5]} rotation={[Math.PI * 0.08, 0, 0]} material={mat.chrome}>
        <torusGeometry args={[0.49, 0.016, 10, 64]} />
      </mesh>

      {/* LEFT EYE dot */}
      <mesh position={[-0.16, 0.14, 0.63]} material={mat.eye}>
        <sphereGeometry args={[0.042, 16, 16]} />
      </mesh>
      {/* eye halo glow ring */}
      <mesh position={[-0.16, 0.14, 0.625]} rotation={[0, 0, 0]} material={mat.eye}>
        <ringGeometry args={[0.045, 0.072, 24]} />
      </mesh>

      {/* RIGHT EYE dot */}
      <mesh position={[0.16, 0.14, 0.63]} material={mat.eye}>
        <sphereGeometry args={[0.042, 16, 16]} />
      </mesh>
      <mesh position={[0.16, 0.14, 0.625]} material={mat.eye}>
        <ringGeometry args={[0.045, 0.072, 24]} />
      </mesh>

      {/* Sensor array — 5 small dots center face */}
      {[-0.1, -0.05, 0, 0.05, 0.1].map((x, i) => (
        <mesh key={i} position={[x, -0.1, 0.64]} material={mat.eye}>
          <sphereGeometry args={[0.013, 8, 8]} />
        </mesh>
      ))}

      {/* Lower face plate — chin module */}
      <mesh position={[0, -0.48, 0.38]} rotation={[0.4, 0, 0]} material={mat.panel}>
        <boxGeometry args={[0.42, 0.16, 0.14]} />
      </mesh>

      {/* Chin ventilation slats */}
      {[-0.1, 0, 0.1].map((x, i) => (
        <mesh key={i} position={[x, -0.52, 0.38]} rotation={[0.4, 0, 0]} material={mat.dimLine}>
          <boxGeometry args={[0.06, 0.012, 0.12]} />
        </mesh>
      ))}

      {/* Left ear/temple panel */}
      <mesh position={[-0.64, 0.08, -0.08]} rotation={[0, 0.55, 0]} material={mat.panel}>
        <boxGeometry args={[0.12, 0.42, 0.22]} />
      </mesh>
      {/* Right ear/temple panel */}
      <mesh position={[0.64, 0.08, -0.08]} rotation={[0, -0.55, 0]} material={mat.panel}>
        <boxGeometry args={[0.12, 0.42, 0.22]} />
      </mesh>

      {/* Left side accent red stripe */}
      <mesh position={[-0.63, 0.08, 0.06]} rotation={[0, 0.55, 0]} material={mat.redAccent}>
        <boxGeometry args={[0.012, 0.3, 0.04]} />
      </mesh>
      {/* Right side accent red stripe */}
      <mesh position={[0.63, 0.08, 0.06]} rotation={[0, -0.55, 0]} material={mat.redAccent}>
        <boxGeometry args={[0.012, 0.3, 0.04]} />
      </mesh>

      {/* Back of head — flat panel */}
      <mesh position={[0, 0, -0.58]} material={mat.mid}>
        <cylinderGeometry args={[0.48, 0.42, 0.14, 32, 1]} />
      </mesh>
    </group>
  )
}

/* ─── NECK ─────────────────────────────────────────────────────────────────── */
function Neck({ mat }) {
  return (
    <group>
      {/* Main neck cylinder */}
      <mesh material={mat.mid} castShadow>
        <cylinderGeometry args={[0.16, 0.22, 0.46, 24, 2]} />
      </mesh>
      {/* Three segment rings */}
      {[-0.14, 0, 0.14].map((y, i) => (
        <mesh key={i} position={[0, y, 0]} material={mat.chrome}>
          <torusGeometry args={[0.19, 0.01, 8, 32]} />
        </mesh>
      ))}
      {/* Neck back cable bundle */}
      <mesh position={[0, 0, -0.14]} material={mat.dark}>
        <cylinderGeometry args={[0.06, 0.06, 0.38, 8]} />
      </mesh>
    </group>
  )
}

/* ─── TORSO ─────────────────────────────────────────────────────────────────── */
function Torso({ mat }) {
  return (
    <group>
      {/* Upper chest body */}
      <mesh material={mat.mid} castShadow>
        <cylinderGeometry args={[0.52, 0.68, 0.9, 8, 1]} />
      </mesh>

      {/* Chest center panel */}
      <mesh position={[0, 0.12, 0.54]} material={mat.panel}>
        <boxGeometry args={[0.48, 0.5, 0.07]} />
      </mesh>

      {/* Chest panel top edge chrome strip */}
      <mesh position={[0, 0.38, 0.57]} material={mat.chrome}>
        <boxGeometry args={[0.42, 0.012, 0.02]} />
      </mesh>

      {/* Chest panel horizontal ribs */}
      {[0.22, 0.08, -0.06, -0.2].map((y, i) => (
        <mesh key={i} position={[0, y, 0.585]} material={mat.dimLine}>
          <boxGeometry args={[0.38, 0.008, 0.018]} />
        </mesh>
      ))}

      {/* RED accent chest stripe — vertical */}
      <mesh position={[0, 0.08, 0.592]} material={mat.redAccent}>
        <boxGeometry args={[0.008, 0.44, 0.018]} />
      </mesh>

      {/* Core emitter dot — chest center */}
      <mesh position={[0, 0.22, 0.605]} material={mat.eye}>
        <sphereGeometry args={[0.022, 16, 16]} />
      </mesh>

      {/* Left chest block */}
      <mesh position={[-0.22, 0.18, 0.52]} material={mat.panel}>
        <boxGeometry args={[0.14, 0.2, 0.06]} />
      </mesh>
      {/* Right chest block */}
      <mesh position={[0.22, 0.18, 0.52]} material={mat.panel}>
        <boxGeometry args={[0.14, 0.2, 0.06]} />
      </mesh>

      {/* Left shoulder cap — smooth half sphere */}
      <mesh position={[-0.78, 0.28, 0]} rotation={[0, 0, -Math.PI * 0.08]} material={mat.glossy} castShadow>
        <sphereGeometry args={[0.38, 48, 32, 0, Math.PI * 2, 0, Math.PI * 0.72]} />
      </mesh>
      {/* Right shoulder cap */}
      <mesh position={[0.78, 0.28, 0]} rotation={[0, 0, Math.PI * 0.08]} material={mat.glossy} castShadow>
        <sphereGeometry args={[0.38, 48, 32, 0, Math.PI * 2, 0, Math.PI * 0.72]} />
      </mesh>

      {/* Shoulder chrome ring — left */}
      <mesh position={[-0.78, 0.1, 0]} rotation={[Math.PI / 2, 0, 0.2]} material={mat.chrome}>
        <torusGeometry args={[0.32, 0.016, 10, 48]} />
      </mesh>
      {/* Shoulder chrome ring — right */}
      <mesh position={[0.78, 0.1, 0]} rotation={[Math.PI / 2, 0, -0.2]} material={mat.chrome}>
        <torusGeometry args={[0.32, 0.016, 10, 48]} />
      </mesh>

      {/* Left upper arm */}
      <mesh position={[-1.05, -0.08, 0]} rotation={[0, 0, -0.12]} material={mat.mid} castShadow>
        <cylinderGeometry args={[0.17, 0.15, 0.75, 20]} />
      </mesh>
      {/* Left elbow ring */}
      <mesh position={[-1.05, -0.46, 0]} rotation={[0, 0, 0.12]} material={mat.chrome}>
        <torusGeometry args={[0.155, 0.016, 8, 32]} />
      </mesh>

      {/* Right upper arm */}
      <mesh position={[1.05, -0.08, 0]} rotation={[0, 0, 0.12]} material={mat.mid} castShadow>
        <cylinderGeometry args={[0.17, 0.15, 0.75, 20]} />
      </mesh>
      {/* Right elbow ring */}
      <mesh position={[1.05, -0.46, 0]} rotation={[0, 0, -0.12]} material={mat.chrome}>
        <torusGeometry args={[0.155, 0.016, 8, 32]} />
      </mesh>

      {/* Waist taper */}
      <mesh position={[0, -0.62, 0]} material={mat.panel}>
        <cylinderGeometry args={[0.56, 0.5, 0.28, 10]} />
      </mesh>

      {/* Waist chrome ring */}
      <mesh position={[0, -0.44, 0]} material={mat.chrome}>
        <torusGeometry args={[0.6, 0.018, 8, 48]} />
      </mesh>

      {/* Bottom cut-off plate */}
      <mesh position={[0, -0.76, 0]} material={mat.dark}>
        <cylinderGeometry args={[0.5, 0.52, 0.06, 10]} />
      </mesh>

      {/* Left side vent panel */}
      <mesh position={[-0.6, -0.04, 0.25]} rotation={[0, -0.3, 0]} material={mat.panel}>
        <boxGeometry args={[0.1, 0.52, 0.08]} />
      </mesh>
      {/* Right side vent panel */}
      <mesh position={[0.6, -0.04, 0.25]} rotation={[0, 0.3, 0]} material={mat.panel}>
        <boxGeometry args={[0.1, 0.52, 0.08]} />
      </mesh>

      {/* Side vent slats — left */}
      {[-0.14, 0, 0.14].map((y, i) => (
        <mesh key={i} position={[-0.62, y, 0.28]} rotation={[0, -0.3, 0]} material={mat.redAccent}>
          <boxGeometry args={[0.008, 0.06, 0.06]} />
        </mesh>
      ))}
      {/* Side vent slats — right */}
      {[-0.14, 0, 0.14].map((y, i) => (
        <mesh key={i} position={[0.62, y, 0.28]} rotation={[0, 0.3, 0]} material={mat.redAccent}>
          <boxGeometry args={[0.008, 0.06, 0.06]} />
        </mesh>
      ))}
    </group>
  )
}

/* ─── ROOT ROBOT ────────────────────────────────────────────────────────────── */
export default function Robot({ mouseRef }) {
  const mat = useMat()
  const rootRef  = useRef()
  const headRef  = useRef()
  const torsoRef = useRef()
  const bootProgress = useRef(0)

  useFrame((state, delta) => {
    // Smooth boot-up transition on reload (eases from 0 to 1 over first ~1.8 seconds)
    if (bootProgress.current < 1) {
      bootProgress.current = Math.min(1, bootProgress.current + delta * 0.7)
    }
    const easeBoot = 1 - Math.pow(1 - bootProgress.current, 3) // cubic ease-out

    const time = state.clock.getElapsedTime()
    // Gentle lifelike breathing and micro-sway
    const idleBreath = Math.sin(time * 1.5) * 0.018
    const idleHeadRoll = Math.sin(time * 0.7) * 0.01

    if (rootRef.current) {
      // Intro rise from slightly below to base position + subtle idle breath
      rootRef.current.position.y = lerp(-1.15, -0.85, easeBoot) + idleBreath
    }

    // Power-up lighting ramp on reload
    if (mat?.eye) {
      mat.eye.emissiveIntensity = lerp(0.8, 4, easeBoot)
    }
    if (mat?.redAccent) {
      mat.redAccent.emissiveIntensity = lerp(0.3, 1.2, easeBoot)
    }

    if (!headRef.current || !torsoRef.current) return
    const mx = mouseRef?.current ? mouseRef.current.x : 0
    const my = mouseRef?.current ? mouseRef.current.y : 0

    // Initial head pitch (starts looking slightly down, powers up to level)
    const bootHeadPitch = lerp(0.16, 0, easeBoot)
    const ty = clamp(mx * HEAD_YAW_MAX,  -HEAD_YAW_MAX,  HEAD_YAW_MAX)
    const tp = clamp(my * HEAD_PITCH_MAX,-HEAD_PITCH_MAX, HEAD_PITCH_MAX)

    headRef.current.rotation.y  = lerp(headRef.current.rotation.y,  ty + idleHeadRoll,  HEAD_LERP)
    headRef.current.rotation.x  = lerp(headRef.current.rotation.x,  -tp + bootHeadPitch, HEAD_LERP)

    const tty = clamp(mx * TORSO_YAW_MAX, -TORSO_YAW_MAX, TORSO_YAW_MAX)
    torsoRef.current.rotation.y = lerp(torsoRef.current.rotation.y, tty, TORSO_LERP)
  })

  return (
    <group ref={rootRef} position={[0, -0.85, 0]} scale={[0.96, 0.96, 0.96]}>
      <group ref={torsoRef}>
        {/* Torso */}
        <group position={[0, 0, 0]}>
          <Torso mat={mat} />
        </group>

        {/* Neck */}
        <group position={[0, 1.12, 0]}>
          <Neck mat={mat} />
        </group>

        {/* Head */}
        <group ref={headRef} position={[0, 1.62, 0]}>
          <Head mat={mat} />
        </group>
      </group>
    </group>
  )
}
