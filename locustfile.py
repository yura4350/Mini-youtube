from locust import HttpUser, task, between

# Simulate users hitting the AuthService API
class AuthServiceUser(HttpUser):
    host = "http://localhost:8003"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")

class DashboardServiceUser(HttpUser):
    host = "http://localhost:8004"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")

class VideoServiceUser(HttpUser):
    host = "http://localhost:8005"
    wait_time = between(1, 3)
    
    @task
    def test_health(self):
        self.client.get("/health")

class CommunicationServiceUser(HttpUser):
    host = "http://localhost:8002"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")

class IntelligenceServiceUser(HttpUser):
    host = "http://localhost:8001"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")

class AdminServiceUser(HttpUser):
    host = "http://localhost:8000"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")