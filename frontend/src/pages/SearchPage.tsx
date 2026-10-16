import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { SearchResponse } from '../types';
import { 
  Search, 
  Clock, 
  User, 
  ArrowRight, 
  Loader2, 
  AlertCircle, 
  Info
} from 'lucide-react';

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchData, setSearchData] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await api.searchVideos(query.trim());
      setSearchData(data);
    } catch (err: any) {
      setError(err.message || 'Search request failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectVideo = (videoUrl: string) => {
    navigate(`/?url=${encodeURIComponent(videoUrl)}`);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Title & Description */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
          Discover & Download
        </h1>
        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 font-normal">
          Search authorized video libraries and stream catalogs. Retrieve high-definition metadata and queue files for processing.
        </p>
      </div>

      {/* Search Input Bar */}
      <form onSubmit={handleSearch} className="max-w-3xl mx-auto">
        <div className="glass-panel rounded-2xl p-2 shadow-xl flex items-center gap-2 focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 bg-white dark:bg-[var(--bg-card)] border border-slate-200 dark:border-white/10">
          <div className="pl-3 text-slate-500 dark:text-slate-400">
            <Search className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search keywords, tutorials, ambient music, podcasts..."
            className="w-full bg-transparent px-2 py-2.5 text-sm sm:text-base text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-sm flex items-center gap-2 transition-all cursor-pointer shrink-0 shadow-md shadow-indigo-600/20"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>Search</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Provider Message / Setup Notice */}
      {searchData && !searchData.is_provider_configured && (
        <div className="max-w-3xl mx-auto p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-700 dark:text-indigo-300 text-xs sm:text-sm flex items-start gap-3">
          <Info className="w-5 h-5 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold block text-slate-900 dark:text-slate-200">Search Provider Configuration</span>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed font-normal">
              {searchData.provider_message ||
                'To enable live video search, configure an authorized YouTube Data API key in your server environment (YOUTUBE_API_KEY). In the meantime, you can paste video URLs directly on the Home page.'}
            </p>
          </div>
        </div>
      )}

      {/* Error Notice */}
      {error && (
        <div className="max-w-3xl mx-auto p-4 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Results Grid */}
      {searchData && searchData.results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-200">
            Results ({searchData.total_count})
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {searchData.results.map((item) => (
              <div
                key={item.id}
                className="glass-panel rounded-2xl overflow-hidden border border-slate-200 dark:border-white/5 hover:border-indigo-500/40 transition-all flex flex-col justify-between group shadow-lg bg-white dark:bg-[var(--bg-card)]"
              >
                <div className="relative aspect-video bg-slate-900 overflow-hidden">
                  {item.thumbnail ? (
                    <img
                      src={item.thumbnail}
                      alt={item.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs text-slate-500">
                      No Preview
                    </div>
                  )}
                  {item.duration_formatted && (
                    <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/80 backdrop-blur-md text-[11px] font-semibold text-white flex items-center gap-1">
                      <Clock className="w-3 h-3 text-cyan-400" />
                      <span>{item.duration_formatted}</span>
                    </div>
                  )}
                </div>

                <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                  <div>
                    <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 line-clamp-2 leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors">
                      {item.title}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 mt-2 font-medium">
                      <User className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400" />
                      <span className="truncate">{item.channel}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleSelectVideo(item.url)}
                    className="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-indigo-600 text-slate-800 hover:text-white dark:bg-slate-800 dark:hover:bg-indigo-600 dark:text-slate-200 text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-sm"
                  >
                    <span>Analyze & Download</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && searchData && searchData.results.length === 0 && searchData.is_provider_configured && (
        <div className="text-center py-12 text-slate-500 space-y-2">
          <p className="text-base font-medium">No results found for "{query}".</p>
          <p className="text-xs">Try different search terms or enter a direct video URL.</p>
        </div>
      )}
    </div>
  );
};
