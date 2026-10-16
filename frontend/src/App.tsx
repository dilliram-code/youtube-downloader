import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { HomePage } from './pages/HomePage';
import { SearchPage } from './pages/SearchPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsModal } from './components/SettingsModal';
import type { AppSettings } from './types';
import { Shield, Film } from 'lucide-react';

const DEFAULT_SETTINGS: AppSettings = {
  theme: 'dark',
  defaultResolution: '1080p',
  defaultFormat: 'mp4',
  defaultMode: 'video_audio',
};

export const App: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>(() => {
    const saved = localStorage.getItem('vidora_settings');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // ignore parse error
      }
    }
    return DEFAULT_SETTINGS;
  });

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Sync theme class to <html>
  useEffect(() => {
    const root = document.documentElement;
    if (settings.theme === 'light') {
      root.classList.add('light');
      root.classList.remove('dark');
    } else {
      root.classList.add('dark');
      root.classList.remove('light');
    }
    localStorage.setItem('vidora_settings', JSON.stringify(settings));
  }, [settings]);

  const toggleTheme = () => {
    setSettings((prev) => ({
      ...prev,
      theme: prev.theme === 'dark' ? 'light' : 'dark',
    }));
  };

  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors duration-200">
        {/* Navigation Bar */}
        <Navbar
          theme={settings.theme === 'light' ? 'light' : 'dark'}
          onToggleTheme={toggleTheme}
          onOpenSettings={() => setIsSettingsOpen(true)}
        />

        {/* Main Application Body */}
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-white/5 py-8 px-4 text-center text-xs text-slate-500">
          <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Film className="w-4 h-4 text-indigo-400" />
              <span className="font-semibold text-slate-300">Vidora Studio</span>
              <span>— Modern Media Downloader & Transcoder</span>
            </div>

            <div className="flex items-center gap-4 text-[11px] text-slate-400">
              <span className="flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-emerald-400" /> Authorized Content Only
              </span>
              <span>•</span>
              <span>No DRM Bypass</span>
              <span>•</span>
              <span>FFmpeg Powered</span>
            </div>
          </div>
        </footer>

        {/* Global Settings Modal */}
        {isSettingsOpen && (
          <SettingsModal
            settings={settings}
            onUpdateSettings={setSettings}
            onClose={() => setIsSettingsOpen(false)}
          />
        )}
      </div>
    </Router>
  );
};

export default App;
