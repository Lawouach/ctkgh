import asyncio
import os
import secrets

import httpx


ACTION = """name: Run Reliably Experiment

on:
  push:
    branches: 
    - main

jobs:
  run-experiment:
    runs-on: ubuntu-latest
    environment: myenv
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip setuptools wheel
        pip install chaostoolkit
    - name: Run experiment
      run : |
        chaos info core
"""

async def make_blob(client: httpx.AsyncClient, owner: str, repo: str,) -> str:
    response = await client.post(
        f"/repos/{owner}/{repo}/git/blobs",
        json={
            "content": ACTION,
            "encoding": "utf-8"
        }
    )
    return response.json()["sha"]


async def make_tree(client: httpx.AsyncClient, owner: str, repo: str, last_commit_sha: str) -> str:
    blob_sha = await make_blob(client, owner, repo)
    response = await client.post(
        f"/repos/{owner}/{repo}/git/trees",
        json={
            "base_tree": last_commit_sha,
            "tree": [
                {
                    "path": f".github/workflows/action-{secrets.token_hex(8)}.yaml",
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                }
            ]
        }
    )
    assert response.status_code == 201, response.json()
    return response.json()["sha"]



async def get_last_sha(client: httpx.AsyncClient, owner: str, repo: str) -> str:
    response = await client.get(
        f"/repos/{owner}/{repo}/git/refs/heads/main"
    )
    return response.json()["object"]["sha"]


async def make_commit(client: httpx.AsyncClient, owner: str, repo: str) -> str:
    last_commit_sha = await get_last_sha(client, owner, repo)
    tree_sha = await make_tree(client, owner, repo, last_commit_sha)

    response = await client.post(
        f"/repos/{owner}/{repo}/git/commits",
        json={
            "message": "hello",
            "parents": [last_commit_sha],
            "tree": tree_sha
        }
    )
    return response.json()["sha"]


async def update_ref(client: httpx.AsyncClient, owner: str, repo: str) -> str:
    sha = await make_commit(client, owner, repo)
    response = await client.post(
        f"/repos/{owner}/{repo}/git/refs/heads/main",
        json={
            "ref": "refs/heads/main",
            "sha": sha
        }
    )
    print(response.json())


async def run(owner: str, repo: str, token: str) -> str:
    async with httpx.AsyncClient() as client:
        client.base_url = "https://api.github.com"
        client.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}"
        }
        await update_ref(client, owner, repo)


if __name__ == "__main__":
    asyncio.run(run("Lawouach", "ctkgh", os.getenv("GITHUB_TOKEN")))
