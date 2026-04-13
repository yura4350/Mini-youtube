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

#### Repository

- GitLab URL: https://coursework.cs.duke.edu/compsci590_2026spring/media_server_team02.git
- Dev host: vcm-52418.vm.duke.edu

#### Branch Workflow

- Typical flow:
	1. Push local changes to GitLab.
	2. Pull branch on VM.
	3. Rebuild/restart containers.

#### VM Setup (for Team Access)

```bash
ssh <netid>@vcm-52418.vm.duke.edu
cd ~/media_server_team02
git fetch origin
git checkout dev
git pull origin dev
docker compose down
docker compose up -d --build
```

#### Local Setup

```bash
git clone https://coursework.cs.duke.edu/compsci590_2026spring/media_server_team02.git
cd media_server_team02
git checkout dev
docker compose up -d --build
```

Open services:

- Frontend: http://localhost:5173
- Video API: http://localhost:8000
- Admin API: http://localhost:8001
- Communication API: http://localhost:8002
- User Accounts API: http://localhost:8003
- Dashboard API: http://localhost:8004


### Notes/Assumptions

- Services are containerized and started with Docker Compose.
- After pulling new code, prefer `docker compose up -d --build` so latest code is applied.

### Impressions

