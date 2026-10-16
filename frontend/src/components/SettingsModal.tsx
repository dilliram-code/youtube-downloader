import React, { useEffect, useState } from 'react';
import type { AppSettings, CapabilitiesResponse } from '../types';
import { api } from '../services/api';
import { 
  Settings as SettingsIcon, 
  X, 
  Check, 
  HardDrive, 
  Film, 
  ShieldCheck
} from 'lucide-react';

interface SettingsModalProps {
  settings: AppSettings;
  onUpdateSettings: (newSettings: AppSettings) => void;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  settings,
  onUpdateSettings,
  onClose,
}) => {
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(null);

  useEffect(() => {
    api.getCapabilities()
      .then(setCapabilities)
      .catch((err) => console.error('Failed to load server capabilities:', err));
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-lg rounded-2xl p-6 sm:p-7 border border-slate-200 dark:border-white/10 shadow-2xl relative space-y-6 bg-white dark:bg-[var(--bg-card)]">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/15 border border-indigo-500/30">
              <SettingsIcon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-slate-100">Application Settings</h3>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-normal">Preferences & Media Engine Status</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* User Preferences */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider mb-2">
              Theme Mode
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(['dark', 'light'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => onUpdateSettings({ ...settings, theme: t })}
                  className={`py-2 px-3 rounded-xl text-xs font-bold uppercase tracking-wider border transition-all cursor-pointer ${
                    settings.theme === t
                      ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 shadow-sm'
                      : 'border-slate-200 dark:border-white/5 bg-slate-100 dark:bg-slate-900/60 text-slate-700 dark:text-slate-400 hover:border-slate-300 dark:hover:border-white/20'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider mb-2">
              Default Resolution Preference
            </label>
            <select
              value={settings.defaultResolution}
              onChange={(e) => onUpdateSettings({ ...settings, defaultResolution: e.target.value })}
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-sm text-slate-900 dark:text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
            >
              <option value="1080p">1080p Full HD (Recommended)</option>
              <option value="720p">720p HD</option>
              <option value="2160p">2160p 4K UHD</option>
              <option value="480p">480p Standard</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider mb-2">
              Default Container
            </label>
            <div className="grid grid-cols-3 gap-2">
              {['mp4', 'webm', 'mp3'].map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => onUpdateSettings({ ...settings, defaultFormat: fmt })}
                  className={`py-2 px-3 rounded-xl text-xs font-bold uppercase tracking-wider border transition-all cursor-pointer ${
                    settings.defaultFormat === fmt
                      ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 shadow-sm'
                      : 'border-slate-200 dark:border-white/5 bg-slate-100 dark:bg-slate-900/60 text-slate-700 dark:text-slate-400 hover:border-slate-300 dark:hover:border-white/20'
                  }`}
                >
                  {fmt}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Server & Engine Diagnostics */}
        <div className="pt-3 border-t border-slate-200 dark:border-white/10 space-y-2.5">
          <span className="text-xs font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider block">
            Processing Engine Health
          </span>

          {capabilities ? (
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/70 border border-slate-200 dark:border-white/5 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400 font-medium flex items-center gap-1.5">
                  <Film className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" /> FFmpeg Pipeline
                </span>
                <span className="text-emerald-700 dark:text-emerald-400 font-bold flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> Operational
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400 font-medium flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" /> FFprobe Inspector
                </span>
                <span className="text-emerald-700 dark:text-emerald-400 font-bold flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> Operational
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400 font-medium flex items-center gap-1.5">
                  <HardDrive className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" /> Max Download Ceiling
                </span>
                <span className="text-slate-800 dark:text-slate-300 font-bold">
                  {capabilities.max_download_size_mb} MB
                </span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic">Querying server capabilities...</div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-2 border-t border-slate-200 dark:border-white/10 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all cursor-pointer shadow-md shadow-indigo-600/20"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
