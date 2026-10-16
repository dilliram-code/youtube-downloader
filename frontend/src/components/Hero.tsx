import React, { useState } from 'react';
import { 
  Sparkles, 
  Clipboard, 
  X, 
  ArrowRight, 
  Loader2, 
  AlertCircle,
  CheckCircle2
} from 'lucide-react';

interface HeroProps {
  url: string;
  onUrlChange: (val: string) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  errorMessage?: string | null;
}

export const Hero: React.FC<HeroProps> = ({
  url,
  onUrlChange,
  onAnalyze,
  isLoading,
  errorMessage,
}) => {
  const [pasteSuccess, setPasteSuccess] = useState(false);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        onUrlChange(text.trim());
        setPasteSuccess(true);
        setTimeout(() => setPasteSuccess(false), 2000);
      }
    } catch (err) {
      console.warn('Clipboard read failed:', err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && url.trim() && !isLoading) {
      onAnalyze();
    }
  };

  const sampleUrls = [
    { label: 'Demo Showcase Video', url: 'https://test-media.local/watch?v=sample' },
    { label: 'YouTube Sample', url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
    { label: 'Vimeo Sample', url: 'https://vimeo.com/76979871' },
  ];

  return (
    <section className="relative pt-12 pb-8 sm:pt-20 sm:pb-12 text-center px-4 max-w-4xl mx-auto">
      {/* Decorative background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-tr from-indigo-500/10 via-cyan-500/10 to-violet-500/10 blur-[100px] -z-10 rounded-full pointer-events-none" />

      {/* Badge */}
      <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400 text-xs font-semibold mb-6">
        <Sparkles className="w-3.5 h-3.5 text-cyan-500 dark:text-cyan-400" />
        <span>Next-Generation Media Downloader & Transcoder</span>
      </div>

      {/* Heading */}
      <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mb-4 leading-tight">
        Your videos. Your quality.{' '}
        <span className="bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 dark:from-cyan-400 dark:via-indigo-400 dark:to-violet-400 bg-clip-text text-transparent">
          Your choice.
        </span>
      </h1>

      {/* Subdescription */}
      <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-8 leading-relaxed font-normal">
        High-fidelity video and audio processing for authorized sources. Combine high-definition streams with lossless FFmpeg encoding, zero DRM bypass, and real-time progress.
      </p>

      {/* Main Input Field Container */}
      <div className="relative max-w-3xl mx-auto">
        <div className="glass-panel rounded-2xl p-2 sm:p-2.5 shadow-xl transition-all duration-200 focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 bg-white dark:bg-[var(--bg-card)]">
          <div className="flex flex-col sm:flex-row items-center gap-2">
            {/* Input with paste and clear icons */}
            <div className="relative flex-1 w-full flex items-center">
              <input
                type="url"
                id="video-url-input"
                value={url}
                onChange={(e) => onUrlChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Paste video URL from YouTube, Vimeo, Archive.org..."
                className="w-full bg-transparent px-4 py-3 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 text-sm sm:text-base focus:outline-none"
                disabled={isLoading}
                autoComplete="off"
              />

              {/* Paste from Clipboard */}
              <button
                type="button"
                onClick={handlePaste}
                title="Paste from clipboard"
                aria-label="Paste from clipboard"
                className="p-2 text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-cyan-400 transition-colors mr-1 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 cursor-pointer"
              >
                {pasteSuccess ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                ) : (
                  <Clipboard className="w-4 h-4" />
                )}
              </button>

              {/* Clear Input */}
              {url && (
                <button
                  type="button"
                  onClick={() => onUrlChange('')}
                  title="Clear input"
                  aria-label="Clear input"
                  className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors mr-2 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Analyze Video Button */}
            <button
              type="button"
              id="analyze-video-btn"
              onClick={onAnalyze}
              disabled={!url.trim() || isLoading}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 text-white font-semibold text-sm sm:text-base shadow-lg shadow-indigo-600/25 hover:shadow-indigo-600/40 hover:opacity-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 shrink-0 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <span>Analyze Video</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error / Validation feedback */}
        {errorMessage && (
          <div className="mt-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-600 dark:text-rose-300 text-sm flex items-start gap-3 text-left">
            <AlertCircle className="w-5 h-5 text-rose-500 dark:text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold block">URL Validation Notice</span>
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Quick Demo links */}
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <span className="text-slate-500 dark:text-slate-500 font-medium">Quick Try:</span>
          {sampleUrls.map((sample) => (
            <button
              key={sample.label}
              type="button"
              onClick={() => {
                onUrlChange(sample.url);
              }}
              className="px-3 py-1 rounded-lg bg-slate-100 dark:bg-white/5 hover:bg-indigo-50 dark:hover:bg-indigo-500/10 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-300 border border-slate-200 dark:border-white/5 hover:border-indigo-400/30 transition-all cursor-pointer font-medium"
            >
              {sample.label}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
};
