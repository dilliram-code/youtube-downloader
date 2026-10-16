import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { JobProgress } from '../types';
import { 
  History as HistoryIcon, 
  Download, 
  Trash2, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  HardDrive, 
  Info, 
  Loader2 
} from 'lucide-react';

export const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<JobProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const items = await api.getHistory();
      setHistory(items);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (jobId: string) => {
    try {
      await api.cancelOrDeleteJob(jobId);
      setHistory((prev) => prev.filter((item) => item.job_id !== jobId));
    } catch (err) {
      console.error('Failed to delete history item:', err);
    }
  };

  const formatBytes = (bytes?: number) => {
    if (!bytes || bytes <= 0) return 'N/A';
    const units = ['B', 'KB', 'MB', 'GB'];
    let b = bytes;
    let i = 0;
    while (b >= 1024 && i < units.length - 1) {
      b /= 1024;
      i++;
    }
    return `${b.toFixed(1)} ${units[i]}`;
  };

  const formatDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <HistoryIcon className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            <span>Download History</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1 font-normal">
            Review past processing operations, inspect artifacts, and retrieve saved media.
          </p>
        </div>

        <button
          onClick={loadHistory}
          className="self-start sm:self-auto px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-bold transition-all cursor-pointer border border-slate-200 dark:border-transparent"
        >
          Refresh History
        </button>
      </div>

      {/* Retention Notice */}
      <div className="p-4 rounded-2xl bg-indigo-50/70 dark:bg-indigo-500/10 border border-indigo-200 dark:border-indigo-500/20 text-xs text-indigo-900 dark:text-indigo-300 flex items-start gap-3">
        <Info className="w-4 h-4 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5" />
        <p className="text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
          <strong className="font-bold text-slate-900 dark:text-white">Storage Policy:</strong> Processed files on the server are automatically retained for 6 hours before scheduled cleanup. Files downloaded to your device remain permanently stored on your local drive.
        </p>
      </div>

      {/* History Items List */}
      {isLoading ? (
        <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-500 dark:text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-600 dark:text-indigo-400" />
          <span className="text-sm font-medium">Loading history...</span>
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-16 glass-panel rounded-2xl border border-slate-200 dark:border-white/5 space-y-3 bg-white dark:bg-[var(--bg-card)]">
          <HistoryIcon className="w-10 h-10 text-slate-400 dark:text-slate-600 mx-auto" />
          <p className="text-base font-bold text-slate-700 dark:text-slate-400">No downloads recorded yet.</p>
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold cursor-pointer transition-all shadow-md shadow-indigo-600/20"
          >
            Start Your First Download
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((job) => {
            const isCompleted = job.status === 'completed';
            const isFailed = job.status === 'failed';

            return (
              <div
                key={job.job_id}
                className="glass-panel rounded-2xl p-4 sm:p-5 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-md bg-white dark:bg-[var(--bg-card)]"
              >
                {/* File info */}
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {isCompleted ? (
                      <span className="px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 text-[11px] font-bold flex items-center gap-1 border border-emerald-500/25">
                        <CheckCircle2 className="w-3 h-3" /> Completed
                      </span>
                    ) : isFailed ? (
                      <span className="px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-700 dark:text-rose-400 text-[11px] font-bold flex items-center gap-1 border border-rose-500/25">
                        <AlertCircle className="w-3 h-3" /> Failed
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-700 dark:text-amber-400 text-[11px] font-bold flex items-center gap-1 border border-amber-500/25">
                        <Clock className="w-3 h-3" /> {job.stage_label}
                      </span>
                    )}

                    <span className="text-xs text-slate-500 font-mono">
                      {formatDate(job.created_at)}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm sm:text-base text-slate-900 dark:text-slate-100 truncate">
                    {job.file_name || 'Processed Media Stream'}
                  </h3>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600 dark:text-slate-400 font-medium">
                    <span className="flex items-center gap-1">
                      <HardDrive className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
                      {formatBytes(job.file_size_bytes || job.total_bytes)}
                    </span>
                    <span>•</span>
                    <span className="font-mono text-slate-500 dark:text-slate-400">ID: {job.job_id}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  {isCompleted && job.download_url && (
                    <a
                      href={job.download_url}
                      download={job.file_name || 'video.mp4'}
                      className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Save File</span>
                    </a>
                  )}

                  <button
                    onClick={() => handleDelete(job.job_id)}
                    title="Remove from history"
                    className="p-2 rounded-xl text-slate-500 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 border border-slate-200 dark:border-white/5 transition-all cursor-pointer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
