import os

from locust import HttpUser, task, between

WAIT = between(0.5, 2.0)

AUTH_EMAIL = os.environ.get("LOCUST_AUTH_EMAIL", "loadtest@example.com")
AUTH_PASSWORD = os.environ.get("LOCUST_AUTH_PASSWORD", "Loadtest1")

USER_ID = os.environ.get("LOCUST_USER_ID", "1")

# Simulate users hitting the AuthService API
class AuthServiceUser(HttpUser):
    
    host = "http://localhost:8003"

    wait_time = WAIT

    def on_start(self):
        self.token = None
        with self.client.post(
            "/auth/login/",
            data={"username": AUTH_EMAIL, "password": AUTH_PASSWORD},
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                self.token = r.json().get("access_token")
            else:
                r.failure(f"login failed: {r.status_code}")

    def _headers(self):
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    @task(4)
    def verify_token(self):
        self.client.get("/verify-token/", headers=self._headers())

    @task(3)
    def profile(self):
        self.client.get("/profile/", headers=self._headers())

    @task(2)
    def list_users_public(self):
        self.client.get("/users/public/")

    @task(1)
    def health(self):
        self.client.get("/health")

class DashboardServiceUser(HttpUser):
    host = "http://localhost:8004"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")

class VideoServiceUser(HttpUser):
    host = "http://localhost:8000"
    wait_time = WAIT

    def on_start(self):
        self.video_id = None
        with self.client.get("/videos", catch_response=True) as r:
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    self.video_id = data[0].get("id")

    @task(4)
    def list_videos(self):
        self.client.get("/videos")

    @task(2)
    def ping(self):
        self.client.get("/videos/ping")

    @task(3)
    def health(self):
        self.client.get("/health")

    @task(2)
    def video_detail(self):
        if not self.video_id:
            return
        self.client.get(f"/videos/{self.video_id}")

    @task(2)
    def transcript(self):
        if not self.video_id:
            return
        self.client.get(f"/videos/{self.video_id}/transcript")

    @task(1)
    def record_view(self):
        if not self.video_id:
            return
        self.client.post(f"/videos/{self.video_id}/view")

class CommunicationServiceUser(HttpUser):
    host = "http://localhost:8002"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")

class IntelligenceServiceUser(HttpUser):
    host = "http://localhost:8005"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")

class AdminServiceUser(HttpUser):
    host = "http://localhost:8001"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")