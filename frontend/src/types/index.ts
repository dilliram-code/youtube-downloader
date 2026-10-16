export type DownloadMode = 'video_audio' | 'audio_only' | 'video_only';

export type JobStatus = 
  | 'queued'
  | 'analyzing'
  | 'downloading'
  | 'merging'
  | 'converting'
  | 'validating'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface QualityOption {
  format_id: string;
  resolution: string;
  width?: number;
  height?: number;
  fps?: number;
  container: string;
  vcodec?: string;
  acodec?: string;
  filesize_bytes?: number;
  estimated_mb?: number;
  has_video: boolean;
  has_audio: boolean;
  requires_merging: boolean;
  is_available: boolean;
  is_recommended: boolean;
  status_label: string;
}

export interface AudioOption {
  format_id: string;
  container: string;
  acodec?: string;
  abr_kbps?: number;
  filesize_bytes?: number;
  estimated_mb?: number;
  quality_label: string;
  is_recommended?: boolean;
}

export interface VideoMetadata {
  id: string;
  url: string;
  title: string;
  description?: string;
  channel?: string;
  channel_url?: string;
  duration_seconds?: number;
  duration_formatted: string;
  thumbnail?: string;
  source_provider: string;
  is_download_permitted: boolean;
  permission_notice?: string;
  video_options: QualityOption[];
  audio_options: AudioOption[];
  best_compatible_video_format_id?: string;
  best_compatible_audio_format_id?: string;
}

export interface JobProgress {
  job_id: string;
  status: JobStatus;
  stage_label: string;
  progress_percent: number;
  downloaded_bytes?: number;
  total_bytes?: number;
  download_speed_bytes?: number;
  eta_seconds?: number;
  error_message?: string;
  file_name?: string;
  file_size_bytes?: number;
  download_url?: string;
  created_at: string;
  updated_at: string;
}

export interface SearchResultItem {
  id: string;
  title: string;
  channel: string;
  duration_seconds?: number;
  duration_formatted: string;
  thumbnail?: string;
  url: string;
  source_provider: string;
  published_at?: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total_count: number;
  has_more: boolean;
  is_provider_configured: boolean;
  provider_message?: string;
}

export interface CapabilitiesResponse {
  app_name: string;
  app_version: string;
  ffmpeg_available: boolean;
  ffprobe_available: boolean;
  max_download_size_mb: number;
  max_concurrent_jobs: number;
  supported_video_containers: string[];
  supported_audio_containers: string[];
  supported_providers: string[];
  search_configured: boolean;
}

export interface AppSettings {
  theme: 'dark' | 'light' | 'system';
  defaultResolution: string;
  defaultFormat: string;
  defaultMode: DownloadMode;
}
