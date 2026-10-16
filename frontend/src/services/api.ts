import type {
  VideoMetadata,
  JobProgress,
  SearchResponse,
  CapabilitiesResponse,
  DownloadMode
} from '../types';

const API_BASE = '/api';

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    const data = await res.json().catch(() => null);

    if (!res.ok) {
      const errMsg = data?.detail || data?.error || `HTTP error ${res.status}`;
      throw new ApiError(errMsg, res.status);
    }

    return data as T;
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Network communication error');
  }
}

export const api = {
  async getCapabilities(): Promise<CapabilitiesResponse> {
    return request<CapabilitiesResponse>('/capabilities');
  },

  async analyzeVideo(url: string): Promise<VideoMetadata> {
    const res = await request<{ success: boolean; error?: string; data?: VideoMetadata }>(
      '/video/analyze',
      {
        method: 'POST',
        body: JSON.stringify({ url }),
      }
    );

    if (!res.success || !res.data) {
      throw new ApiError(res.error || 'Failed to analyze video');
    }

    return res.data;
  },

  async createDownload(payload: {
    url: string;
    mode: DownloadMode;
    resolution?: string;
    format_id?: string;
    target_container: string;
    audio_format_id?: string;
    audio_quality?: string;
  }): Promise<JobProgress> {
    return request<JobProgress>('/downloads', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getJobStatus(jobId: string): Promise<JobProgress> {
    return request<JobProgress>(`/downloads/${jobId}`);
  },

  async cancelOrDeleteJob(jobId: string): Promise<void> {
    await request<{ success: boolean }>(`/downloads/${jobId}`, {
      method: 'DELETE',
    });
  },

  async searchVideos(query: string, page = 1, limit = 10): Promise<SearchResponse> {
    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      limit: limit.toString(),
    });
    return request<SearchResponse>(`/video/search?${params.toString()}`);
  },

  async getHistory(): Promise<JobProgress[]> {
    return request<JobProgress[]>('/history');
  },
};
