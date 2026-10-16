import React from 'react';
import type { VideoMetadata } from '../types';
import { Clock, User, Globe, AlertTriangle, ShieldCheck } from 'lucide-react';

interface VideoCardProps {
  metadata: VideoMetadata;
}

export const VideoCard: React.FC<VideoCardProps> = ({ metadata }) => {
  return (
    <div className="glass-panel rounded-2xl overflow-hidden border border-slate-200 dark:border-white/10 shadow-xl transition-all bg-white dark:bg-[var(--bg-card)]">
      <div className="flex flex-col lg:flex-row">
        {/* Thumbnail with overlay duration */}
        <div className="relative lg:w-2/5 shrink-0 bg-slate-900 aspect-video lg:aspect-auto flex items-center justify-center overflow-hidden">
          {metadata.thumbnail ? (
            <img
              src={metadata.thumbnail}
              alt={metadata.title}
              className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div className="text-slate-400 text-sm font-medium">No Thumbnail Available</div>
          )}

          {/* Duration Badge */}
          {metadata.duration_formatted && (
            <div className="absolute bottom-3 right-3 px-2 py-1 rounded-md bg-black/80 backdrop-blur-md text-white text-xs font-semibold flex items-center gap-1 shadow-md">
              <Clock className="w-3 h-3 text-cyan-400" />
              <span>{metadata.duration_formatted}</span>
            </div>
          )}

          {/* Provider Badge */}
          <div className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-slate-900/80 text-white text-[11px] font-medium border border-white/20 uppercase tracking-wider flex items-center gap-1.5 shadow-md">
            <Globe className="w-3 h-3 text-indigo-400" />
            <span>{metadata.source_provider}</span>
          </div>
        </div>

        {/* Video Details */}
        <div className="p-5 sm:p-6 lg:w-3/5 flex flex-col justify-between">
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 line-clamp-2 mb-2 leading-snug">
              {metadata.title}
            </h2>

            {/* Creator / Channel info */}
            <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-slate-600 dark:text-slate-400 mb-4">
              <div className="flex items-center gap-1.5">
                <User className="w-4 h-4 text-indigo-500 dark:text-indigo-400" />
                <span className="font-semibold text-slate-700 dark:text-slate-300">{metadata.channel || 'Unknown Creator'}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span className="text-emerald-600 dark:text-emerald-400 font-medium">Authorized Media Stream</span>
              </div>
            </div>

            {/* Description excerpt */}
            {metadata.description && (
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 line-clamp-2 mb-4 leading-relaxed font-normal">
                {metadata.description}
              </p>
            )}
          </div>

          {/* Permission limitation notice if not permitted */}
          {!metadata.is_download_permitted && (
            <div className="mt-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-300 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block">Download Limitation</span>
                <span>
                  {metadata.permission_notice ||
                    'Direct media download is not permitted for this content under publisher access restrictions.'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
