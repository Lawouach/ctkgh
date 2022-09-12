import secrets

from ghapi.all import GhApi


ACTION = """name: Run Reliably Experiment

on:
  push:
    branches: 
    - main

jobs:
  build:
    runs-on: ubuntu-latest
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

def make_blob(api: GhApi) -> str:
    return api.git.create_blob(content=ACTION, encoding="utf-8")["sha"]

def make_tree(api: GhApi, blob_sha: str) -> str:
    last_commit_sha = api.git.get_ref("heads/main")["object"]["sha"]
    name = secrets.token_hex(8)
    return api.git.create_tree(
        base_treestring=last_commit_sha,
        tree=[{
            "path": f".github/workflows/{name}",
            "mode": "100644",
            "type": "blob",
            "sha": blob_sha
        }]
    )["sha"]


def make_commit(api: GhApi, tree_sha: str) -> str:
    return api.git.create_tree(
        message="hello",
        tree=tree_sha
    )["sha"]


def run():
    api = GhApi(owner="Lawouach", repo="ctkgh")
    sha = make_blob(api)
    sha = make_tree(api, sha)
    make_commit(api, sha)


if __name__ == "__main__":
    run()
