import React, { useEffect, useState } from 'react';
import type { JobProgress } from '../types';
import { api } from '../services/api';
import { 
  CheckCircle2, 
  AlertCircle, 
  X, 
  RotateCcw, 
  Download, 
  Loader2, 
  Activity,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface ProgressModalProps {
  jobId: string;
  onClose: () => void;
  onRetry: () => void;
}

export const ProgressModal: React.FC<ProgressModalProps> = ({
  jobId,
  onClose,
  onRetry,
}) => {
  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const data = await api.getJobStatus(jobId);
        setProgress(data);

        // Keep polling if still in active state
        if (
          data.status !== 'completed' &&
          data.status !== 'failed' &&
          data.status !== 'cancelled'
        ) {
          timer = setTimeout(poll, 750);
        }
      } catch (err) {
        console.error('Error polling job status:', err);
      }
    };

    poll();
    return () => clearTimeout(timer);
  }, [jobId]);

  const handleCancel = async () => {
    setIsCancelling(true);
    try {
      await api.cancelOrDeleteJob(jobId);
      const data = await api.getJobStatus(jobId);
      setProgress(data);
    } catch (err) {
      console.error('Failed to cancel job:', err);
    } finally {
      setIsCancelling(false);
    }
  };

  const formatBytes = (bytes?: number) => {
    if (!bytes || bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let b = bytes;
    let i = 0;
    while (b >= 1024 && i < units.length - 1) {
      b /= 1024;
      i++;
    }
    return `${b.toFixed(1)} ${units[i]}`;
  };

  const formatSpeed = (bytesPerSec?: number) => {
    if (!bytesPerSec || bytesPerSec <= 0) return null;
    return `${formatBytes(bytesPerSec)}/s`;
  };

  const isFinished = progress?.status === 'completed';
  const isFailed = progress?.status === 'failed';
  const isCancelled = progress?.status === 'cancelled';
  const isActive = progress && !isFinished && !isFailed && !isCancelled;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-lg rounded-2xl p-6 sm:p-7 border border-slate-200 dark:border-white/10 shadow-2xl relative space-y-6 bg-white dark:bg-[var(--bg-card)]">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/15 border border-indigo-500/30">
              <Activity className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-slate-100">Media Processing Job</h3>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">ID: {jobId}</span>
            </div>
          </div>

          {(isFinished || isFailed || isCancelled) && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Content State */}
        {progress ? (
          <div className="space-y-5">
            {/* Stage Label & Percentage */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isActive && <Loader2 className="w-4 h-4 text-cyan-600 dark:text-cyan-400 animate-spin" />}
                {isFinished && <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />}
                {isFailed && <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400" />}
                <span className="font-bold text-sm sm:text-base text-slate-800 dark:text-slate-200">
                  {progress.stage_label}
                </span>
              </div>
              <span className="font-mono text-sm font-bold text-indigo-600 dark:text-indigo-400">
                {Math.round(progress.progress_percent)}%
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-2.5 bg-slate-200 dark:bg-slate-900 rounded-full overflow-hidden border border-slate-300 dark:border-white/5">
              <div
                className={`h-full transition-all duration-300 rounded-full ${
                  isFailed
                    ? 'bg-rose-500'
                    : isFinished
                    ? 'bg-emerald-500'
                    : 'bg-gradient-to-r from-indigo-500 via-cyan-400 to-indigo-400'
                }`}
                style={{ width: `${Math.max(5, progress.progress_percent)}%` }}
              />
            </div>

            {/* Live Metrics Grid */}
            {isActive && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-2 text-xs">
                <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-white/5">
                  <span className="text-slate-500 dark:text-slate-400 block font-medium">Downloaded</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {formatBytes(progress.downloaded_bytes)}
                    {progress.total_bytes ? ` / ${formatBytes(progress.total_bytes)}` : ''}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-white/5">
                  <span className="text-slate-500 dark:text-slate-400 block font-medium">Speed</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {formatSpeed(progress.download_speed_bytes) || 'Calculating...'}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-white/5 col-span-2 sm:col-span-1">
                  <span className="text-slate-500 dark:text-slate-400 block font-medium">ETA</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {progress.eta_seconds ? `${progress.eta_seconds}s remaining` : 'Estimating...'}
                  </span>
                </div>
              </div>
            )}

            {/* Error Message Display */}
            {isFailed && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-300 text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold">
                  <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                  <span>Processing Error</span>
                </div>
                <p>{progress.error_message || 'An unexpected error occurred during processing.'}</p>

                <button
                  onClick={() => setShowDiagnostics(!showDiagnostics)}
                  className="text-[11px] text-rose-600 dark:text-rose-400 underline flex items-center gap-1 mt-1 cursor-pointer font-medium"
                >
                  {showDiagnostics ? 'Hide Technical Details' : 'Show Technical Details'}
                  {showDiagnostics ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>

                {showDiagnostics && (
                  <pre className="p-2 rounded bg-slate-100 dark:bg-black/50 text-[10px] text-slate-800 dark:text-slate-400 font-mono overflow-x-auto mt-2 border border-slate-200 dark:border-transparent">
                    {JSON.stringify(progress, null, 2)}
                  </pre>
                )}
              </div>
            )}

            {/* Completed Output Card */}
            {isFinished && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 text-xs space-y-3">
                <div className="flex items-center gap-2 font-bold text-emerald-700 dark:text-emerald-400 text-sm">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  <span>Media Ready For Download</span>
                </div>
                <div className="text-slate-700 dark:text-slate-300">
                  <span className="block font-bold truncate text-slate-900 dark:text-slate-100">{progress.file_name}</span>
                  <span className="text-slate-500 dark:text-slate-400">
                    File Size: {formatBytes(progress.file_size_bytes)}
                  </span>
                </div>

                <a
                  href={`/api/downloads/${jobId}/file`}
                  download={progress.file_name || 'video.mp4'}
                  className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-lg shadow-emerald-600/30 flex items-center justify-center gap-2 transition-all cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  <span>Save File to Device</span>
                </a>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 flex flex-col items-center justify-center gap-3 text-slate-500 dark:text-slate-400 text-sm">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-600 dark:text-indigo-400" />
            <span className="font-medium">Connecting to job scheduler...</span>
          </div>
        )}

        {/* Modal Controls */}
        <div className="pt-2 border-t border-slate-200 dark:border-white/10 flex items-center justify-end gap-3">
          {isActive && (
            <button
              onClick={handleCancel}
              disabled={isCancelling}
              className="px-4 py-2 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs font-bold transition-all cursor-pointer"
            >
              {isCancelling ? 'Cancelling...' : 'Cancel Operation'}
            </button>
          )}

          {isFailed && (
            <button
              onClick={onRetry}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-md"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry Job</span>
            </button>
          )}

          {(isFinished || isFailed || isCancelled) && (
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-bold transition-all cursor-pointer"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
