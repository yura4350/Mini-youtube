Media Server
====

This project implements a Media Server composed of several micro-services.

Name: 

### Timeline

Start Date: 

Finish Date: 

Hours Spent:


### Tutorial, LLMs, and other Code used

- GitHub Copilot (GPT-5.3-Codex) for setup/debug support.
- Claude Code (Sonnet-4.6) for assistance in implementing `GET /admin/metrics`.
- Claude Code (Sonnet-4.6) for suggestions on handling logs in admin API. Utilized MemoryHandler as suggested.

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

Ensure your machine can reach `vcm-52418.vm.duke.edu` on these ports (may require Duke network access).

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
- **Frontend can't reach APIs:** Ensure the VM's firewall allows connections on ports 8000-8004

Main class: `src/video_crud_service/main.py`, `src/admin_service/main.py`, etc.

Data files needed: Database is auto-initialized by PostgreSQL container

Known Bugs:


### Notes/Assumptions

- Services are containerized and started with Docker Compose.
- After pulling new code, prefer `docker compose up -d --build` so latest code is applied.

### Impressions

