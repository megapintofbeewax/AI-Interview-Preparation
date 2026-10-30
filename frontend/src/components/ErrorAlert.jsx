import React from 'react';

/**
 * Reusable dark glassmorphic error alert with action buttons.
 * Enforces the rule: "Never show raw technical errors to the user."
 */
export default function ErrorAlert({
  title,
  message,
  onRetry,
  retryLabel = "Try Again",
  secondaryAction,
  secondaryLabel,
  className = ""
}) {
  if (!message) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`p-4 rounded-card bg-red-950/30 backdrop-blur-xl border border-red-500/30 text-left shadow-2xl relative overflow-hidden ${className}`}
    >
      {/* Decorative red indicator line */}
      <div className="absolute top-0 left-0 bottom-0 w-1 bg-red-500/80 shadow-[0_0_12px_rgba(239,68,68,0.5)]" />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3.5 pl-2">
        <div className="space-y-1">
          {title && (
            <h4 className="text-sm font-semibold text-red-200 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
              <span>{title}</span>
            </h4>
          )}
          <p className="text-xs text-red-300/90 leading-relaxed font-normal">
            {message}
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="min-h-[38px] px-3.5 py-1.5 text-xs font-semibold text-red-200 bg-red-500/20 border border-red-500/40 rounded-control hover:bg-red-500/30 transition-all duration-fast cursor-pointer shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
            >
              {retryLabel}
            </button>
          )}
          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction}
              className="min-h-[38px] px-3.5 py-1.5 text-xs font-semibold text-[#FAFAF5] bg-white/[0.08] border border-white/10 rounded-control hover:bg-white/[0.15] transition-all duration-fast cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
            >
              {secondaryLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
