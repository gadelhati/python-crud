"""Locust load profile for an already provisioned test/staging environment.

Required environment variables:
  PERF_USERNAME, PERF_PASSWORD
Optional:
  PERF_TARGET_HOST (Locust's --host can be used instead)
"""

import os

from locust import HttpUser, between, task


class CrudApiUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        username = os.environ["PERF_USERNAME"]
        password = os.environ["PERF_PASSWORD"]
        response = self.client.post(
            "/login",
            json={"username": username, "password": password},
            name="/login",
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(4)
    def list_users(self) -> None:
        self.client.get("/user?page=1&limit=20", headers=self.headers, name="/user")

    @task(2)
    def list_roles(self) -> None:
        self.client.get("/role?page=1&limit=20", headers=self.headers, name="/role")

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="/health")
