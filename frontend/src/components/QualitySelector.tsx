import React, { useState, useEffect } from 'react';
import type { 
  DownloadMode, 
  VideoMetadata, 
  QualityOption, 
  AudioOption 
} from '../types';
import { 
  Film, 
  Music, 
  Video, 
  Check, 
  Download, 
  Sparkles,
  Info
} from 'lucide-react';

interface QualitySelectorProps {
  metadata: VideoMetadata;
  onStartDownload: (params: {
    mode: DownloadMode;
    resolution?: string;
    format_id?: string;
    target_container: string;
    audio_format_id?: string;
    audio_quality?: string;
  }) => void;
  isStarting: boolean;
}

export const QualitySelector: React.FC<QualitySelectorProps> = ({
  metadata,
  onStartDownload,
  isStarting,
}) => {
  const [mode, setMode] = useState<DownloadMode>('video_audio');
  const [selectedResolution, setSelectedResolution] = useState<string>('');
  const [selectedVideoOption, setSelectedVideoOption] = useState<QualityOption | null>(null);
  const [selectedAudioOption, setSelectedAudioOption] = useState<AudioOption | null>(null);
  const [targetContainer, setTargetContainer] = useState<string>('mp4');

  // Initialize selection from metadata
  useEffect(() => {
    if (metadata.video_options.length > 0) {
      const recommended = metadata.video_options.find((o) => o.is_recommended) || metadata.video_options[0];
      setSelectedVideoOption(recommended);
      setSelectedResolution(recommended.resolution);
    }

    if (metadata.audio_options.length > 0) {
      const recAudio = metadata.audio_options.find((a) => a.is_recommended) || metadata.audio_options[0];
      setSelectedAudioOption(recAudio);
    }
  }, [metadata]);

  // Adjust container when mode switches
  const handleModeChange = (newMode: DownloadMode) => {
    setMode(newMode);
    if (newMode === 'audio_only') {
      setTargetContainer('mp3');
    } else {
      setTargetContainer('mp4');
    }
  };

  const handleResolutionSelect = (option: QualityOption) => {
    setSelectedVideoOption(option);
    setSelectedResolution(option.resolution);
  };

  const handleSubmit = () => {
    if (!metadata.is_download_permitted) return;

    onStartDownload({
      mode,
      resolution: selectedResolution,
      format_id: selectedVideoOption?.format_id,
      target_container: targetContainer,
      audio_format_id: selectedAudioOption?.format_id,
      audio_quality: selectedAudioOption?.quality_label || 'best',
    });
  };

  const totalEstimatedMb = () => {
    if (mode === 'audio_only') {
      return selectedAudioOption?.estimated_mb || null;
    }
    const vMb = selectedVideoOption?.estimated_mb || 0;
    const aMb = (mode === 'video_audio' && selectedVideoOption?.requires_merging)
      ? (selectedAudioOption?.estimated_mb || 0)
      : 0;
    const sum = vMb + aMb;
    return sum > 0 ? Math.round(sum * 10) / 10 : null;
  };

  const isHighResolution = selectedResolution === '2160p' || selectedResolution === '1440p';
  const estMb = totalEstimatedMb();

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-200 dark:border-white/10 shadow-2xl space-y-6 bg-white dark:bg-[var(--bg-card)]">
      {/* Download Mode Tabs */}
      <div>
        <label className="block text-xs font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider mb-3">
          1. Select Download Mode
        </label>
        <div className="grid grid-cols-3 gap-2 p-1.5 bg-slate-100 dark:bg-slate-900/80 rounded-xl border border-slate-200 dark:border-white/5">
          <button
            type="button"
            onClick={() => handleModeChange('video_audio')}
            className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              mode === 'video_audio'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-white/5'
            }`}
          >
            <Film className="w-4 h-4 shrink-0" />
            <span>Video & Audio</span>
          </button>

          <button
            type="button"
            onClick={() => handleModeChange('audio_only')}
            className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              mode === 'audio_only'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-white/5'
            }`}
          >
            <Music className="w-4 h-4 shrink-0" />
            <span>Audio Only</span>
          </button>

          <button
            type="button"
            onClick={() => handleModeChange('video_only')}
            className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              mode === 'video_only'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-white/5'
            }`}
          >
            <Video className="w-4 h-4 shrink-0" />
            <span>Video Only</span>
          </button>
        </div>
      </div>

      {/* Video Quality Options */}
      {mode !== 'audio_only' && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-xs font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider">
              2. Available Video Resolutions
            </label>
            <span className="text-[11px] text-cyan-600 dark:text-cyan-400 font-semibold flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              Source Authentic Only
            </span>
          </div>

          {metadata.video_options.length === 0 ? (
            <p className="text-sm text-slate-500 italic">No discrete video streams discovered.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {metadata.video_options.map((opt) => {
                const isSelected = selectedVideoOption?.format_id === opt.format_id;
                const is4K = opt.resolution === '2160p';
                return (
                  <div
                    key={opt.format_id}
                    onClick={() => handleResolutionSelect(opt)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50 dark:bg-indigo-500/15 shadow-sm'
                        : 'border-slate-200 dark:border-white/5 bg-slate-50/70 dark:bg-slate-900/60 hover:border-slate-300 dark:hover:border-white/20 hover:bg-slate-100 dark:hover:bg-slate-900'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900 dark:text-slate-100">{opt.resolution}</span>
                        {is4K && (
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/30">
                            4K UHD
                          </span>
                        )}
                        {opt.is_recommended && (
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border border-cyan-500/30">
                            Best Compatible
                          </span>
                        )}
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />}
                    </div>

                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-600 dark:text-slate-400 font-medium">
                      {opt.estimated_mb && (
                        <span>~{opt.estimated_mb} MB</span>
                      )}
                      {opt.vcodec && (
                        <span className="truncate max-w-[100px]">{opt.vcodec.split('.')[0]}</span>
                      )}
                      <span className={`text-[11px] font-semibold ${opt.has_audio ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400'}`}>
                        {opt.has_audio ? 'Audio Included' : 'Separate Audio'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Audio Stream Selection */}
      {mode === 'audio_only' && (
        <div>
          <label className="block text-xs font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider mb-3">
            2. Audio Quality Preference
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {metadata.audio_options.map((audio) => {
              const isSelected = selectedAudioOption?.format_id === audio.format_id;
              return (
                <div
                  key={audio.format_id}
                  onClick={() => setSelectedAudioOption(audio)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50 dark:bg-indigo-500/15 shadow-sm'
                      : 'border-slate-200 dark:border-white/5 bg-slate-50/70 dark:bg-slate-900/60 hover:border-slate-300 dark:hover:border-white/20 hover:bg-slate-100 dark:hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-sm text-slate-900 dark:text-slate-100">{audio.quality_label}</span>
                    {isSelected && <Check className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-400 font-medium">
                    <span>Source: {audio.container.toUpperCase()}</span>
                    {audio.estimated_mb && <span>~{audio.estimated_mb} MB</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Target Container Format Selection */}
      <div>
        <label className="block text-xs font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider mb-3">
          3. Output Container Format
        </label>
        <div className="flex flex-wrap gap-2">
          {mode === 'audio_only'
            ? ['mp3', 'm4a', 'opus', 'wav'].map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => setTargetContainer(fmt)}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold uppercase tracking-wider transition-all cursor-pointer ${
                    targetContainer === fmt
                      ? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-800 dark:text-cyan-300 border border-cyan-400 dark:border-cyan-500/40 shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-900/60 text-slate-700 dark:text-slate-400 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/20'
                  }`}
                >
                  {fmt}
                </button>
              ))
            : ['mp4', 'webm', 'mkv'].map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => setTargetContainer(fmt)}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold uppercase tracking-wider transition-all cursor-pointer ${
                    targetContainer === fmt
                      ? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-800 dark:text-cyan-300 border border-cyan-400 dark:border-cyan-500/40 shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-900/60 text-slate-700 dark:text-slate-400 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/20'
                  }`}
                >
                  {fmt}
                </button>
              ))}
        </div>
      </div>

      {/* Large File & 4K Alert */}
      {isHighResolution && (
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-3">
          <Info className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">High Resolution Download</span>
            <span className="font-normal">
              4K / QHD media files require substantial bandwidth and temporary storage. Automatic stream merging will execute with hardware-efficient stream copying.
            </span>
          </div>
        </div>
      )}

      {/* Summary Banner & Start Button */}
      <div className="pt-3 border-t border-slate-200 dark:border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-left w-full sm:w-auto">
          <span className="text-xs text-slate-500 dark:text-slate-400 block font-medium">Selected Configuration:</span>
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-slate-200 mt-0.5">
            <span>{mode === 'audio_only' ? 'Audio' : selectedResolution || 'Auto'}</span>
            <span>•</span>
            <span className="uppercase text-cyan-600 dark:text-cyan-400">{targetContainer}</span>
            {estMb && (
              <>
                <span>•</span>
                <span className="text-slate-600 dark:text-slate-400 font-normal">~{estMb} MB</span>
              </>
            )}
          </div>
        </div>

        <button
          type="button"
          id="start-download-btn"
          onClick={handleSubmit}
          disabled={!metadata.is_download_permitted || isStarting}
          className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 text-white font-bold text-sm sm:text-base shadow-xl shadow-indigo-600/30 hover:shadow-indigo-600/50 hover:opacity-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
        >
          <Download className="w-5 h-5" />
          <span>{isStarting ? 'Initiating Job...' : 'Start Download'}</span>
        </button>
      </div>
    </div>
  );
};
