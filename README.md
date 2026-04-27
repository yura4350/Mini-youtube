Media Server
====

This project implements a Media Server composed of several micro-services.

Name: MiniTube — Iurii Beliaev, Temesgen Tewolde, Changmin Shin, Zhao Huang

### Timeline

Start Date: March 18, 2026

Finish Date: April 27, 2026

Hours Spent: 120 hours total (30 hours per teammate)


### Tutorial, LLMs, and other Code used

- GitHub Copilot (GPT-5.3-Codex) for setup/debug support.
- Claude Code (Sonnet-4.6) for assistance in implementing `GET /admin/metrics`.
- Claude Code (Sonnet-4.6) for suggestions on handling logs in admin API. Utilized MemoryHandler as suggested.
- Claude Code (Opus) for improving video thumbnail generation to use a representative frame instead of the first frame.

### Resource Attributions

FastAPI docs, SQLAlchemy docs, PostgreSQL docs, Docker docs.

### Running the Program

#### Prerequisites
- Docker and Docker Compose installed on the VM
- Git for cloning the repository
- VM should be accessible over the network (check firewall rules)

#### Starting the Services

1. **Clone the repository on the VM:**
   ```bash
   git clone https://coursework.cs.duke.edu/compsci590_2026spring/media_server_team02.git
   cd media_server_team02
   git checkout dev  # Switch to the dev branch
   ```

2. **Start all services using Docker Compose:**
   ```bash
   docker-compose up -d
   ```
   This will start:
   - PostgreSQL database
   - Video CRUD service (port 8000)
   - Admin service (port 8001)
   - Communication service (port 8002)
   - User accounts & preferences service (port 8003)
   - Dashboard service (port 8004)
   - Intelligence service (port 8005)
   - Frontend (Vue.js) on port 5173

3. **Verify services are running:**
   ```bash
   docker-compose ps
   ```
   All containers should show "Up" status with healthy health checks.

#### Accessing the Services from Team Machines

The dev branch is hosted on `vcm-52418.vm.duke.edu`. Access services using:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | `http://vcm-52418.vm.duke.edu:5173` | Web UI |
| Video API | `http://vcm-52418.vm.duke.edu:8000` | Video CRUD operations |
| Admin API | `http://vcm-52418.vm.duke.edu:8001` | Admin functions & metrics |
| Communication API | `http://vcm-52418.vm.duke.edu:8002` | Communication service |
| User Accounts & Prefs API | `http://vcm-52418.vm.duke.edu:8003` | User management |
| Dashboard API | `http://vcm-52418.vm.duke.edu:8004` | Dashboard data |
| Intelligence API | `http://vcm-52418.vm.duke.edu:8005` | AI summarize/tagging service |

Ensure your machine can reach `vcm-52418.vm.duke.edu` on these ports (may require Duke network access).

The **main** branch is hosted on `vcm-52527.vm.duke.edu`. Access services using:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | `http://vcm-52527.vm.duke.edu:5173` | Web UI |
| Video API | `http://vcm-52527.vm.duke.edu:8000` | Video CRUD operations |
| Admin API | `http://vcm-52527.vm.duke.edu:8001` | Admin functions & metrics |
| Communication API | `http://vcm-52527.vm.duke.edu:8002` | Communication service |
| User Accounts & Prefs API | `http://vcm-52527.vm.duke.edu:8003` | User management |
| Dashboard API | `http://vcm-52527.vm.duke.edu:8004` | Dashboard data |
| Intelligence API | `http://vcm-52527.vm.duke.edu:8005` | AI summarize/tagging service |

Ensure your machine can reach `vcm-52527.vm.duke.edu` on these ports (may require Duke network access).

#### Stopping the Services

```bash
docker-compose down
```

To remove all data (including database):
```bash
docker-compose down -v
```

#### Viewing Application Logs

```bash
docker-compose logs -f  # All services
docker-compose logs -f video  # Specific service (video, admin, communication, etc.)
```

#### Troubleshooting

- **Services won't start:** Check `docker-compose logs` for error messages
- **Port conflicts:** Modify port mappings in `docker-compose.yml` if ports are already in use
- **Database connection issues:** Verify DATABASE_URL environment variables match the postgres service credentials
- **Frontend can't reach APIs:** Ensure the VM's firewall allows connections on ports 8000-8005

#### Automatic ASR (Video Transcription)

- The `video` service can automatically transcribe uploaded videos using `faster-whisper`.
- It is enabled in `docker-compose.yml` with:
  - `ASR_ENABLED=true`
  - `ASR_MODEL_SIZE=tiny`
  - `ASR_COMPUTE_TYPE=int8`
- The Docker build installs ASR dependencies only when `INSTALL_ASR_DEPS=1` is set (already configured for `video` service).

#### Real AI Summary (OpenAI)

- The `intelligence` service supports real LLM summarization via OpenAI.
- Setup:
  - `cp .env.example .env`
  - Fill your own key and model in `.env`.
- Configure these environment variables before `docker compose up`:
  - `OPENAI_API_KEY=your_key_here`
  - `OPENAI_SUMMARY_MODEL=gpt-4o-mini` (or your preferred model)
  - Optional:
    - `OPENAI_SUMMARY_ENABLED=true`
    - `OPENAI_SUMMARY_MAX_OUTPUT_TOKENS=220`
- If `OPENAI_API_KEY` is missing or the OpenAI call fails, the service automatically falls back to rules-based summary.
- Quick check:
  - `GET /ai/health` on intelligence service returns `provider: openai` when configured.

#### AI Tag Taxonomy

- Canonical tag design and generation flow are documented in:
  - `doc/AI_TAG_TAXONOMY.md`
- AI tag generation is constrained by active canonical tags (instead of free-form tags), then stored in `video_tags`.

Main class: `src/video_crud_service/main.py`, `src/admin_service/main.py`, etc.

Data files needed: Database is auto-initialized by PostgreSQL container

### Testing the program

#### Concurrency and Load Testing (on the `vcm-52527.vm.duke.edu`)

- Admin Dashboard (only /health endpoint) - no need for large throughput
  - 250 concurrent users+

- Video Service
  - 100+, 500 concurrent shut down the service

- Auth Service
  - 70+, some errors at 100+ concurrent users

- Intelligence Service
  - 500+ concurrent users

- Communication Service
  - 500+ concurrent users

- Dashboard Service
  - 500+ concurrent users


### Notes/Assumptions

- Services are containerized and started with Docker Compose.
- After pulling new code, prefer `docker compose up -d --build` so latest code is applied.

### Known bugs
- If hosted on the Duke VM, SMTP doesn't work (most likely due to the university restrictions)

### Impressions
