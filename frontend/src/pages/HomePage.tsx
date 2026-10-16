import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Hero } from '../components/Hero';
import { VideoCard } from '../components/VideoCard';
import { QualitySelector } from '../components/QualitySelector';
import { ProgressModal } from '../components/ProgressModal';
import type { VideoMetadata, DownloadMode } from '../types';
import { api } from '../services/api';

export const HomePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);

  // Active Download Job State
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isStartingDownload, setIsStartingDownload] = useState(false);

  // If navigated from search with pre-filled URL
  useEffect(() => {
    const urlParam = searchParams.get('url');
    if (urlParam) {
      setUrl(urlParam);
      handleAnalyze(urlParam);
    }
  }, [searchParams]);

  const handleAnalyze = async (targetUrl?: string) => {
    const analyzeTarget = targetUrl || url;
    if (!analyzeTarget.trim() || isLoading) return;

    setIsLoading(true);
    setErrorMessage(null);
    setMetadata(null);

    try {
      const data = await api.analyzeVideo(analyzeTarget.trim());
      setMetadata(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to inspect media stream.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartDownload = async (params: {
    mode: DownloadMode;
    resolution?: string;
    format_id?: string;
    target_container: string;
    audio_format_id?: string;
    audio_quality?: string;
  }) => {
    if (!metadata) return;

    setIsStartingDownload(true);
    try {
      const job = await api.createDownload({
        url: metadata.url,
        mode: params.mode,
        resolution: params.resolution,
        format_id: params.format_id,
        target_container: params.target_container,
        audio_format_id: params.audio_format_id,
        audio_quality: params.audio_quality,
      });

      setActiveJobId(job.job_id);
    } catch (err: any) {
      alert(`Download request failed: ${err.message}`);
    } finally {
      setIsStartingDownload(false);
    }
  };

  return (
    <div className="space-y-10 pb-16">
      {/* Hero Input Section */}
      <Hero
        url={url}
        onUrlChange={(val) => {
          setUrl(val);
          if (errorMessage) setErrorMessage(null);
        }}
        onAnalyze={() => handleAnalyze()}
        isLoading={isLoading}
        errorMessage={errorMessage}
      />

      {/* Main Content Area: Video Preview & Quality Selector */}
      {metadata && (
        <div className="max-w-4xl mx-auto px-4 space-y-6 animate-fadeIn">
          {/* Video Metadata Card */}
          <VideoCard metadata={metadata} />

          {/* Quality & Format Selection Panel */}
          <QualitySelector
            metadata={metadata}
            onStartDownload={handleStartDownload}
            isStarting={isStartingDownload}
          />
        </div>
      )}

      {/* Real-time Progress Modal */}
      {activeJobId && (
        <ProgressModal
          jobId={activeJobId}
          onClose={() => setActiveJobId(null)}
          onRetry={() => {
            const currentJob = activeJobId;
            setActiveJobId(null);
            setTimeout(() => setActiveJobId(currentJob), 100);
          }}
        />
      )}
    </div>
  );
};
