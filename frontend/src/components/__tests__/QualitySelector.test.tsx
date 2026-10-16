import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QualitySelector } from '../QualitySelector';
import type { VideoMetadata } from '../../types';

const mockMetadata: VideoMetadata = {
  id: 'test1234',
  url: 'https://test-media.local/watch?v=sample',
  title: 'Test Showcase Video',
  channel: 'Studio Labs',
  duration_seconds: 120,
  duration_formatted: '2:00',
  source_provider: 'mock',
  is_download_permitted: true,
  video_options: [
    {
      format_id: 'v_1080p',
      resolution: '1080p',
      container: 'mp4',
      vcodec: 'h264',
      estimated_mb: 45.2,
      has_video: true,
      has_audio: false,
      requires_merging: true,
      is_available: true,
      is_recommended: true,
      status_label: 'Requires merging',
    },
    {
      format_id: 'v_720p',
      resolution: '720p',
      container: 'mp4',
      vcodec: 'h264',
      estimated_mb: 22.1,
      has_video: true,
      has_audio: true,
      requires_merging: false,
      is_available: true,
      is_recommended: false,
      status_label: 'Ready',
    },
  ],
  audio_options: [
    {
      format_id: 'a_192k',
      container: 'm4a',
      abr_kbps: 192,
      quality_label: '192 kbps (High)',
      estimated_mb: 4.5,
      is_recommended: true,
    },
  ],
};

describe('QualitySelector Component', () => {
  it('renders download mode buttons and available resolutions without fabricating', () => {
    render(
      <QualitySelector
        metadata={mockMetadata}
        onStartDownload={vi.fn()}
        isStarting={false}
      />
    );

    expect(screen.getByText('Video & Audio')).toBeInTheDocument();
    expect(screen.getByText('Audio Only')).toBeInTheDocument();
    expect(screen.getByText('Video Only')).toBeInTheDocument();

    // Must show genuine available resolutions
    expect(screen.getAllByText('1080p').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('720p')).toBeInTheDocument();

    // Must NOT show unprovided resolutions (like 4K or 144p)
    expect(screen.queryByText('2160p')).not.toBeInTheDocument();
    expect(screen.queryByText('144p')).not.toBeInTheDocument();
  });

  it('submits selected parameters when Start Download is clicked', () => {
    const handleStartDownload = vi.fn();

    render(
      <QualitySelector
        metadata={mockMetadata}
        onStartDownload={handleStartDownload}
        isStarting={false}
      />
    );

    const downloadBtn = screen.getByRole('button', { name: /Start Download/i });
    fireEvent.click(downloadBtn);

    expect(handleStartDownload).toHaveBeenCalledWith(
      expect.objectContaining({
        mode: 'video_audio',
        resolution: '1080p',
        target_container: 'mp4',
      })
    );
  });
});
