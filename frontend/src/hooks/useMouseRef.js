import { useEffect, useRef } from 'react'

/**
 * Returns a ref that always holds the latest normalised mouse position.
 * x: -1 (left) → +1 (right)
 * y: -1 (bottom) → +1 (top)
 *
 * No React state is ever set — zero re-renders on mouse move.
 */
export function useMouseRef() {
  const mouseRef = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const handler = (e) => {
      mouseRef.current.x = (e.clientX / window.innerWidth) * 2 - 1
      mouseRef.current.y = -(e.clientY / window.innerHeight) * 2 + 1
    }
    window.addEventListener('mousemove', handler, { passive: true })
    return () => window.removeEventListener('mousemove', handler)
  }, [])

  return mouseRef
}
