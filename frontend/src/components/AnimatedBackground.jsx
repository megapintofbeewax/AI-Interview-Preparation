import React from 'react';

/**
 * AnimatedBackground
 * 
 * macOS-inspired atmospheric living background with black and amber tones.
 * Features 4 enormous, softly blurred gradient layers drifting asynchronously:
 * - Layer 1: Primary Amber Field (#D97706, ~35s cycle)
 * - Layer 2: Burnt-Orange Wave (#EA580C, ~42s cycle)
 * - Layer 3: Secondary Amber Glow (#F59E0B, ~30s cycle)
 * - Layer 4: Deep Warm Shadow & Drift (#92400E, ~45s cycle)
 * 
 * Includes an organic dark vignette to maintain a predominantly black aesthetic
 * (approx. 90% velvety dark, <=10% warm visible light) and an architectural subtle grid.
 * Persistent across all client routes without remounting or resetting.
 */
export default function AnimatedBackground() {
  return (
    <div 
      aria-hidden="true" 
      className="fixed inset-0 pointer-events-none -z-20 overflow-hidden bg-[#09090B]"
    >
      {/* ========================================================
          LAYER 1: PRIMARY AMBER FIELD (#D97706)
          Enormous diffused amber region positioned upper-left / upper-middle.
          Main warm illumination with soft, dissolved edges.
          ======================================================== */}
      <div 
        className="macos-wave-layer animate-macos-wave-1 absolute -top-[18%] left-[8%] w-[95vw] max-w-[1400px] h-[75vh] max-h-[900px] rounded-[50%]"
        style={{
          background: 'radial-gradient(ellipse 65% 55% at 50% 50%, rgba(217, 119, 6, 0.16) 0%, rgba(217, 119, 6, 0.08) 32%, rgba(217, 119, 6, 0.02) 58%, transparent 75%)',
          filter: 'blur(110px)',
          transform: 'translate3d(0, 0, 0)',
          willChange: 'transform',
        }}
      />

      {/* ========================================================
          LAYER 2: BURNT-ORANGE WAVE (#EA580C)
          Broad, blurred burnt-orange region positioned lower-right / lower-middle.
          Creates depth, warmth, and gentle contrast.
          ======================================================== */}
      <div 
        className="macos-wave-layer animate-macos-wave-2 absolute -bottom-[22%] -right-[12%] w-[100vw] max-w-[1500px] h-[80vh] max-h-[950px] rounded-[50%]"
        style={{
          background: 'radial-gradient(ellipse 60% 55% at 50% 50%, rgba(234, 88, 12, 0.13) 0%, rgba(234, 88, 12, 0.065) 35%, rgba(234, 88, 12, 0.015) 60%, transparent 78%)',
          filter: 'blur(125px)',
          transform: 'translate3d(0, 0, 0)',
          willChange: 'transform',
        }}
      />

      {/* ========================================================
          LAYER 3: SECONDARY AMBER GLOW (#F59E0B)
          Very large, low-opacity bright-amber region positioned mid-left / center.
          Adds atmospheric multi-source lighting depth.
          ======================================================== */}
      <div 
        className="macos-wave-layer animate-macos-wave-3 absolute top-[32%] -left-[18%] w-[85vw] max-w-[1300px] h-[70vh] max-h-[850px] rounded-[50%]"
        style={{
          background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(245, 158, 11, 0.09) 0%, rgba(245, 158, 11, 0.045) 35%, rgba(245, 158, 11, 0.01) 60%, transparent 75%)',
          filter: 'blur(100px)',
          transform: 'translate3d(0, 0, 0)',
          willChange: 'transform',
        }}
      />

      {/* ========================================================
          LAYER 4: DEEP WARM SHADOW & DRIFT (#92400E)
          Subtle dark-amber / warm charcoal contour positioned upper-right.
          Overlaps the other layers to create dimensional darkness and organic contour.
          ======================================================== */}
      <div 
        className="macos-wave-layer animate-macos-wave-4 absolute top-[12%] right-[5%] w-[90vw] max-w-[1350px] h-[75vh] max-h-[900px] rounded-[50%]"
        style={{
          background: 'radial-gradient(ellipse 65% 55% at 50% 50%, rgba(146, 64, 14, 0.08) 0%, rgba(146, 64, 14, 0.035) 40%, rgba(24, 24, 27, 0.015) 65%, transparent 80%)',
          filter: 'blur(135px)',
          transform: 'translate3d(0, 0, 0)',
          willChange: 'transform',
        }}
      />

      {/* ========================================================
          ATMOSPHERIC VIGNETTE OVERLAY
          Ensures the outer perimeter and corners melt smoothly into deep #09090B black.
          Prevents gradient clipping and guarantees 90% dark visual dominance.
          ======================================================== */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 85% 75% at 50% 50%, transparent 30%, rgba(9, 9, 11, 0.35) 70%, rgba(9, 9, 11, 0.85) 100%)',
        }}
      />

      {/* ========================================================
          SUBTLE ARCHITECTURAL GRID OVERLAY
          48px grid with fine 2% translucency for sleek depth texture.
          ======================================================== */}
      <div 
        className="absolute inset-0 opacity-[0.38] pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(to right, rgba(255, 255, 255, 0.022) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.022) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />
    </div>
  );
}
