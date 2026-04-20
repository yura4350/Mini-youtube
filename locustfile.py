from locust import HttpUser, task, between

# Simulate users hitting the AuthService API
class AuthServiceUser(HttpUser):
    host = "http://localhost:8003"
    wait_time = between(1, 3)

    @task
    def test_health(self):
        self.client.get("/health")