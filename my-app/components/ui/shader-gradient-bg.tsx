'use client'

import React, { useState, useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import { cn } from '@/lib/utils'

// Dynamic imports — prevents SSR errors and keeps WebGL out of the initial JS bundle
const ShaderGradientCanvas = dynamic(
  () => import('@shadergradient/react').then((mod) => mod.ShaderGradientCanvas),
  { ssr: false }
)

const ShaderGradient = dynamic(
  () => import('@shadergradient/react').then((mod) => mod.ShaderGradient),
  { ssr: false }
)

export interface ShaderGradientBgProps {
  children?: React.ReactNode
  className?: string
  /** HEX color 1 */
  color1?: string
  /** HEX color 2 */
  color2?: string
  /** HEX color 3 */
  color3?: string
  type?: 'waterPlane' | 'plane' | 'sphere'
  /** Animation speed — keep low (≤0.2) for GPU efficiency */
  uSpeed?: number
  /** Wave density — keep ≤1.5 for smooth frame rate */
  uDensity?: number
  /** Wave strength */
  uStrength?: number
  grain?: 'on' | 'off'
  /** Paste a URL from shadergradient.co/customize to override all color/type props */
  controlUrl?: string
}

export function ShaderGradientBg({
  children,
  className,
  color1 = '#ff5900',
  color2 = '#0029ff',
  color3 = '#ff00a0',
  type = 'waterPlane',
  uSpeed = 0.15,
  uDensity = 1.0,
  uStrength = 0.3,
  grain = 'off',
  controlUrl,
}: ShaderGradientBgProps) {
  const [isInView, setIsInView] = useState(true)
  const [mounted, setMounted] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Pause WebGL rendering when component leaves viewport — saves GPU frames
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => setIsInView(entry.isIntersecting),
      { threshold: 0.05 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  // Honour OS reduced-motion preference
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setPrefersReducedMotion(window.matchMedia('(prefers-reduced-motion: reduce)').matches)
    }
  }, [])

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      {/* ── WebGL Canvas (lazy, client-only, only while in view) ── */}
      {mounted && isInView && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            zIndex: 0,
            pointerEvents: 'none',
            overflow: 'hidden',
          }}
        >
          <ShaderGradientCanvas
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
            }}
          >
            {controlUrl ? (
              <ShaderGradient control="query" urlString={controlUrl} />
            ) : (
              <ShaderGradient
                type={type}
                animate={prefersReducedMotion ? 'off' : 'on'}
                uSpeed={uSpeed}
                uStrength={uStrength}
                uDensity={uDensity}
                color1={color1}
                color2={color2}
                color3={color3}
                grain={grain}
                cDistance={32}
                cPolarAngle={125}
              />
            )}
          </ShaderGradientCanvas>
        </div>
      )}

      {/* ── CSS Fallback — instant visual while Three.js initialises ── */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          opacity: 0.4,
          filter: 'blur(60px)',
          background: `radial-gradient(circle at 50% 50%, ${color1}, ${color2}, ${color3})`,
        }}
      />

      {/* ── Content sits above ── */}
      <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>
    </div>
  )
}
