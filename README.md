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

- **FastAPI** — framework used to build all backend microservices (REST endpoints, dependency injection, request validation)
- **SQLAlchemy** — ORM used for all database models and queries across services
- **PostgreSQL** — relational database for storing users, videos, transcripts, messages, and tags
- **Docker / Docker Compose** — containerization and multi-service orchestration for local dev and VM deployment
- **Vue.js / Vite** — frontend framework and build tool for the web UI
- **Pydantic** — data validation and schema definitions for API request/response models
- **PyJWT** — JWT token generation and verification for user authentication
- **faster-whisper** — automatic speech recognition (ASR) for video transcription
- **OpenAI API** — LLM-based video summarization in the intelligence service
- **WebSockets** — real-time messaging in the communication service
- **Locust** — load and concurrency testing framework
- **GitLab CI/CD** — automated test pipeline and deployment to Duke VMs

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

To do stress testing for a particular service, run `locust -f locustfile.py [Desired Service]ServiceUser`

- Admin Dashboard (only /health endpoint) - no need for large throughput
  - 100+ concurrent users

- Video Service
  - 100+ concurrent users

- Auth Service
  - 100+ concurrent users

- Intelligence Service
  - 100+ concurrent users

- Communication Service
  - 100+ concurrent users

- Dashboard Service
  - 100+ concurrent users


### Microservice API Overview

| Service | Port | Owner | Responsibilities |
|---------|------|-------|-----------------|
| **Video CRUD** | 8000 | Temesgen | Video upload, streaming/playback, metadata CRUD, thumbnail generation, ASR transcription, view counting, AI tagging |
| **Admin** | 8001 | Changmin | System health metrics, application logs, user management (ban/delete), content deletion |
| **Communication** | 8002 | Zhao | Real-time WebSocket chat, new-video and subscription notifications, notification inbox |
| **User Accounts & Prefs** | 8003 | Iurii | Registration, login/logout, JWT auth, profile management, password reset, UI settings (light/dark mode) |
| **Dashboard** | 8004 | Changmin | Video search, watch history, subscription feed, video recommendations |
| **Intelligence** | 8005 | Zhao | AI-generated video summaries (OpenAI or rules-based fallback), canonical tag taxonomy, auto-tagging |

### Security and Data

- **Authentication:** JWT tokens issued on login, verified on every protected endpoint. Tokens include user ID and role (`user` / `admin`).
- **Password storage:** bcrypt hashing via passlib — plaintext passwords are never stored.
- **Role-based access:** Admin-only endpoints (user management, content deletion, metrics) reject non-admin tokens with 403.
- **Authorization fix (Sprint 4):** Video update/delete endpoints originally trusted the `uploader_id` supplied by the client. This was identified as a security issue (#97) and fixed so the server now extracts the user identity from the JWT instead.
- **Input validation:** Pydantic schemas enforce types, required fields, and password strength (minimum length, character requirements) at the API boundary.
- **Data integrity:** Foreign key constraints and `TRUNCATE ... CASCADE` patterns ensure referential consistency across videos, transcripts, summaries, and tags.

### Assumptions

- Video files are stored on the local filesystem (bind-mounted Docker volume) rather than object storage like S3. This simplifies deployment but limits horizontal scaling.
- A single shared PostgreSQL instance serves all microservices. Each service uses its own set of tables but shares the same DB container.
- SMTP email (password reset emails) is assumed to work in local development. On Duke VMs, outbound SMTP is blocked by university firewall — the reset flow degrades gracefully (token is generated and logged, but the email is not delivered).
- AI tagging is constrained to a canonical tag taxonomy rather than free-form tags. This keeps tags consistent and searchable at the cost of flexibility.
- Video transcription (`faster-whisper`) runs synchronously after upload on the `tiny` model for speed. Accuracy is reduced compared to larger models, which was an acceptable trade-off for demo performance.
- The frontend is built with environment variables baked in at Docker build time (`VITE_*`). This means the VM hostname must be set before building — runtime config injection was out of scope.

### Challenging Bug: Avatar Not Reflecting Across the App

After implementing avatar upload, avatars displayed correctly on the profile page but appeared as the default placeholder everywhere else (video cards, player page, comments). The bug was traced to the fact that the frontend was reading the avatar URL from the video's uploader metadata cached at upload time, not from the live user profile. The video service stored a snapshot of the uploader's avatar path at upload time. The fix was to have the frontend fetch the uploader's current profile from the user accounts service using the `uploader_id` on the video, rather than relying on the stale embedded field. This required adding a cross-service call in the frontend and adjusting the video card and player components to resolve avatars dynamically.

### Project Management: Roles and Sprint Milestones

**Sprint 1 (Mar 23 – Mar 28): Core Infrastructure**
- Iurii: User authentication backend — registration, login, password hashing, JWT management (User Accounts & Preferences service)
- Temesgen: Basic video upload API, metadata storage, video playback endpoint (Video CRUD service)
- Zhao: Frontend scaffolding — create account page, login page, main dashboard, video upload page, video player page, search bar
- Changmin: Dashboard & Search API skeleton, Admin Dashboard API skeleton

**Sprint 2 (Mar 27 – Apr 5): Backend Foundation & Integration**
- Iurii: Database schema finalization, SQLite → PostgreSQL migration, Docker setup, user profile backend
- Temesgen: Frontend–backend integration for video CRUD
- Changmin: Frontend–backend integration for dashboard and admin APIs
- Zhao: Communication service backend (notifications)
- Everyone: Write tests for their respective services

**Sprint 3 (Apr 3 – Apr 15): Feature Completion**
- Iurii: User accounts & preferences continued (profile UI, settings, privacy, avatar, admin seeding), CI/CD Docker container
- Temesgen: Overall application flow — connecting services end-to-end, video CRUD test suite
- Zhao: Communication API completion (real-time chat, subscriptions), Intelligence API (AI summarization, auto-tagging)
- Changmin: Dashboard and Admin API completion, overall application integration

**Sprint 4 (Apr 10 – Apr 27): Polish, Stability, and Bug Fixes**
- Bug bash fixes across all services
- Iurii: CI/CD pipeline (VM deployment), stress testing, dark/light mode CSS, email debug, service refactor
- Temesgen: User profile/channel page, avatar bug fix, video–user mapping, JWT authorization security fix, video delete fix
- Changmin: Subscriber list, search history, subscription UI, unique username enforcement, concurrency/rate limit testing
- Zhao: Intelligence auto-tagging automation, UI fixes (cache clearing, login redirect, password strength, chat navigation)

**Feature Milestones**

| Feature | Status |
|---------|--------|
| User registration & login with JWT | Done |
| Video upload, playback, metadata CRUD | Done |
| Search with keyword matching | Done |
| User dashboard & profile | Done |
| Real-time WebSocket chat | Done |
| AI summarization & auto-tagging | Done |
| Admin dashboard (health, metrics, logs, user management) | Done |
| Concurrency / stress testing | Done |
| CI/CD pipeline with VM deployment | Done |
| Rate limiting | Not completed |
| Email verification | Not completed (SMTP blocked on Duke VMs) |

### How LLMs Were Used

LLMs were used as a coding assistant throughout the project — not to generate large features wholesale, but to accelerate specific implementation tasks and unblock problems. Key uses:

- **GitHub Copilot** — inline autocomplete during routine backend and frontend coding (boilerplate, repetitive patterns).
- **Claude Code** — used for three specific tasks where we knew what we wanted but needed help with the implementation details:
  - Implementing `GET /admin/metrics` — we described the endpoint requirements and used the output as a starting point, then reviewed and adapted it.
  - Structuring log handling in the admin service — Claude suggested `MemoryHandler` as a pattern for buffering log records, which we evaluated and adopted.
  - Improving video thumbnail generation — Claude identified the `ffmpeg thumbnail` filter as the right tool to avoid blank first-frames, a detail we wouldn't have found quickly in the docs.
- **OpenAI API (in-product)** — the intelligence service itself calls OpenAI to generate video summaries. This is a feature, not a development tool.

In all cases, LLM-generated code was reviewed before merging. We did not use LLMs for security-critical code (auth, JWT handling) or database schema design, where we wanted full understanding and control.

### Notes/Assumptions

- Services are containerized and started with Docker Compose.
- After pulling new code, prefer `docker compose up -d --build` so latest code is applied.

### Known bugs
- If hosted on the Duke VM, SMTP doesn't work (due to the university restrictions (`nc -vz smtp.gmail.com 587` does not return anything and times out on the VM, but works locally))

### Impressions
