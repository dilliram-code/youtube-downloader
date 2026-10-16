# Vidora — Modern Video Downloader & Media Studio

Vidora is a modern, elegant, full-stack web application designed for downloading, transcoding, and processing media from authorized sources. Built with a dark-first glassmorphism design system on the frontend and an asynchronous Python/FastAPI and FFmpeg processing pipeline on the backend.

---

## 🌟 Key Features

- **Intuitive Studio UI**:
  - Dark-first theme with deep charcoal/midnight backgrounds, cyan/violet accents, and subtle glassmorphic panels.
  - Light/Dark theme toggle with persistent user preference.
  - Large URL input with clipboard paste button, clear button, and keyboard Enter execution.
  - Quick-try demo showcase buttons for immediate offline/mock testing.

- **Authentic Stream & Quality Selection**:
  - Genuine resolution selection: 2160p (4K UHD), 1440p (QHD), 1080p (Full HD), 720p (HD), 480p, 360p, 240p, 144p.
  - *Never fabricates options*: only displays resolutions and streams provided by the source.
  - Displays video codecs (H.264, VP9, AV1), audio codecs (AAC, Opus, MP3), and estimated file sizes.
  - 3 Download Modes: **Video with Audio**, **Audio Only**, and **Video Only**.
  - Output containers: **MP4**, **WebM**, **MKV** for video; **MP3**, **M4A**, **Opus**, **WAV** for audio.

- **Reliable FFmpeg Processing Engine**:
  - Automatically combines separate video and audio streams.
  - Uses hardware-efficient stream copying (`-c copy`) whenever codecs are compatible with the target container.
  - Performs safe transcoding only when the target container requires it.
  - Validates output files with `ffprobe` before serving to verify stream integrity and non-zero duration.

- **Background Job Scheduler & Live Monitoring**:
  - Bounded concurrency with `asyncio.Semaphore` and execution timeouts.
  - Detailed stage tracking: `queued` → `analyzing` → `downloading` → `merging` → `converting` → `validating` → `completed`.
  - Real-time download progress with percentage, speed, bytes downloaded, and estimated time remaining (ETA).
  - User cancellation support with automatic temporary file cleanup.
  - Server retention sweeper for periodic cleanup of expired media files.

- **Search & Discovery**:
  - Integrated search catalog with thumbnail previews, duration, channel name, and 1-click analysis.
  - Supports authorized YouTube Data API v3 provider, or displays clear setup instructions if unconfigured.

- **Persistent Download History**:
  - SQLite database (with PostgreSQL support for production).
  - View past jobs, final file sizes, completion dates, direct download actions, and history removal.

- **Robust Security & SSRF Protection**:
  - Validates URL syntax and enforces allowed provider domains.
  - Protects against SSRF by checking IP literals and resolving hostnames against private/loopback/link-local/multicast networks (e.g., `127.0.0.0/8`, `10.0.0.0/8`, `169.254.0.0/16`, `172.16.0.0/12`, `192.168.0.0/16`, `::1`).
  - Safe subprocess execution without shell interpolation (`shell=False`).
  - Path traversal protection on all file endpoints.
  - Strictly compliant: does not bypass DRM, access controls, or private video restrictions.

---

## 🛠 Technology Stack

### Frontend
- **Framework**: React 19 + TypeScript
- **Bundler**: Vite 8
- **Styling**: Tailwind CSS v4 + Custom Glassmorphism System
- **Icons**: Lucide React
- **Routing**: React Router v7
- **Testing**: Vitest + React Testing Library + JSDOM

### Backend
- **Runtime**: Python 3.12 / 3.13
- **Web Framework**: FastAPI
- **Data Validation**: Pydantic v2 & Pydantic-Settings
- **ORM & Database**: SQLAlchemy 2.0 (Async) + SQLite (`aiosqlite`) / PostgreSQL
- **Media Engine**: yt-dlp, FFmpeg 8+, FFprobe
- **Testing**: Pytest + pytest-asyncio + httpx (ASGI Transport)

---

## 📋 Prerequisites

Ensure you have the following installed:
1. **Python 3.12+**
2. **Node.js 20+** and **npm**
3. **FFmpeg & FFprobe**:
   - **macOS** (via Homebrew):
     ```bash
     brew install ffmpeg
     ```
   - **Ubuntu / Debian**:
     ```bash
     sudo apt-get update && sudo apt-get install -y ffmpeg
     ```
   - **Windows** (via Chocolatey or Winget):
     ```powershell
     choco install ffmpeg
     # or
     winget install "Gyan.FFmpeg"
     ```

---

## 🚀 Quick Start (Local Development)

### 1. Clone Repository & Setup Environment
```bash
git clone <repository_url>
cd youTubeDownloader
cp .env.example backend/.env
```

### 2. Backend Setup
```bash
# Initialize virtual environment
python3 -m venv backend/.venv

# Activate venv & install dependencies
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# Run backend server (runs on port 8080)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8080 --reload
```
*API documentation is available at `http://localhost:8080/docs`.*

### 3. Frontend Setup
In a new terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server (runs on port 5173 with proxy to backend)
npm run dev
```

Open `http://localhost:5173/` in your browser.

---

## 🧪 Running Automated Tests

### Run Backend Tests (18 tests)
```bash
backend/.venv/bin/pytest backend/tests/
```
Tests cover:
- SSRF prevention, IP resolution, URL validator, safe filename sanitization
- Stream selection algorithm (resolution constraints, codec matching, container rules)
- FFmpeg stream merging, audio extraction, conversion, and FFprobe output validation with synthetic media
- Background job manager lifecycle, cancellation, and progress updates
- FastAPI REST endpoints (`/health`, `/capabilities`, `/analyze`, `/downloads`, `/search`)

### Run Frontend Tests (5 tests)
```bash
cd frontend
npm test
```
Tests cover:
- Hero URL input, keyboard Enter handling, and validation feedback
- QualitySelector options rendering, authentic resolution checks, and download trigger

### Build Frontend for Production
```bash
cd frontend
npm run build
```

---

## 🐳 Docker Deployment

To launch the full production stack with Docker Compose:

```bash
docker-compose up --build -d
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8080`

---

## ⚙️ Environment Variables Reference

| Variable | Default | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `Vidora` | Application branding name |
| `APP_ENV` | `development` | Environment mode (`development` / `production`) |
| `PORT` | `8080` | Backend API server listening port |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Permitted CORS origins |
| `DATABASE_URL` | `sqlite+aiosqlite:///./vidora.db` | Database connection string |
| `FFMPEG_PATH` | `/opt/homebrew/bin/ffmpeg` or `ffmpeg` | Path to FFmpeg binary |
| `FFPROBE_PATH` | `/opt/homebrew/bin/ffprobe` or `ffprobe` | Path to FFprobe binary |
| `MAX_DOWNLOAD_SIZE_MB` | `2048` | Maximum download size ceiling (2 GB) |
| `MAX_CONCURRENT_JOBS` | `3` | Maximum concurrent background processing jobs |
| `JOB_RETENTION_HOURS` | `6` | Media file retention period before automatic deletion |
| `YOUTUBE_API_KEY` | `""` | Optional Google Cloud API key for YouTube Data API v3 search |

---

## 🛡 Security & Compliance Architecture

1. **SSRF Defense**: The backend analyzes and resolves all target hostnames before sending requests. Loopback (`127.0.0.0/8`), private RFC1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local (`169.254.0.0/16`), and non-standard schemes are blocked immediately.
2. **Subprocess Isolation**: Subprocess calls to FFmpeg and FFprobe use structured argument arrays without shell interpolation (`shell=False`).
3. **Path Traversal Protection**: Output files are verified against the absolute storage directory root using `os.path.realpath` before being served.
4. **Authorized Retrieval**: Only public, permitted media streams are processed. DRM-protected and authenticated private streams are detected and flagged with explanatory notices.

---

## 📄 License
MIT License. Created for modern media engineering and authorized video processing.
