"""Persistence layer for master_cv.yaml, applications.yaml, generated_versions.yaml.

Two backends:
- LocalYAMLStorage: reads/writes files directly under data/. Used for local dev
  and for `streamlit run app.py` on your own machine.
- GitHubYAMLStorage: reads/writes the same files via the GitHub Contents API, so
  edits made on Streamlit Community Cloud (whose filesystem is ephemeral and
  reset on every reboot) persist as commits to the repo instead of being lost.

get_storage() picks GitHubYAMLStorage automatically when a GITHUB_TOKEN is
available (e.g. via Streamlit secrets on the cloud deployment), and falls back
to LocalYAMLStorage otherwise.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

from models import MasterCV, Application, GeneratedVersion

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
GENERATED_DOCS_DIR = "generated_documents"
MASTER_CV_FILE = "master_cv.yaml"
APPLICATIONS_FILE = "applications.yaml"
GENERATED_VERSIONS_FILE = "generated_versions.yaml"


class LocalYAMLStorage:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.project_root = data_dir.parent

    def _read(self, filename: str) -> dict | list | None:
        path = self.data_dir / filename
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _write(self, filename: str, data: dict | list, commit_message: str = "") -> None:
        path = self.data_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=100)

    # --- master CV ---
    def load_master_cv(self) -> Optional[MasterCV]:
        raw = self._read(MASTER_CV_FILE)
        return MasterCV.from_dict(raw) if raw else None

    def save_master_cv(self, cv: MasterCV, commit_message: str = "Update master CV") -> None:
        self._write(MASTER_CV_FILE, cv.to_dict(), commit_message)

    # --- applications tracker ---
    def load_applications(self) -> list[Application]:
        raw = self._read(APPLICATIONS_FILE) or []
        return [Application.from_dict(a) for a in raw]

    def save_applications(self, apps: list[Application], commit_message: str = "Update applications tracker") -> None:
        self._write(APPLICATIONS_FILE, [a.to_dict() for a in apps], commit_message)

    # --- generated versions log ---
    def load_generated_versions(self) -> list[GeneratedVersion]:
        raw = self._read(GENERATED_VERSIONS_FILE) or []
        return [GeneratedVersion.from_dict(v) for v in raw]

    def save_generated_versions(self, versions: list[GeneratedVersion], commit_message: str = "Log generated version") -> None:
        self._write(GENERATED_VERSIONS_FILE, [v.to_dict() for v in versions], commit_message)

    # --- generated document files (CV/cover letter .docx per application) ---
    def save_generated_document(self, relative_path: str, content: bytes, commit_message: str = "") -> None:
        path = self.project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)


class GitHubYAMLStorage:
    """Same interface as LocalYAMLStorage, backed by the GitHub Contents API.

    Requires:
      - GITHUB_TOKEN: a fine-grained PAT with contents:write on the target repo
      - GITHUB_REPO: "owner/repo" (e.g. "luisya4505/Sistema_CV")
      - GITHUB_BRANCH: defaults to "main"
    """

    def __init__(self, token: str, repo_name: str, branch: str = "main", data_dir: str = "data"):
        from github import Github  # local import: only needed on the cloud path

        self._gh = Github(token)
        self._repo = self._gh.get_repo(repo_name)
        self._branch = branch
        self._data_dir = data_dir

    def _path(self, filename: str) -> str:
        return f"{self._data_dir}/{filename}"

    def _read(self, filename: str) -> dict | list | None:
        try:
            content_file = self._repo.get_contents(self._path(filename), ref=self._branch)
        except Exception:
            return None
        return yaml.safe_load(content_file.decoded_content.decode("utf-8"))

    def _write(self, filename: str, data: dict | list, commit_message: str) -> None:
        text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100)
        path = self._path(filename)
        try:
            existing = self._repo.get_contents(path, ref=self._branch)
            self._repo.update_file(path, commit_message or f"Update {filename}", text, existing.sha, branch=self._branch)
        except Exception:
            self._repo.create_file(path, commit_message or f"Create {filename}", text, branch=self._branch)

    def load_master_cv(self) -> Optional[MasterCV]:
        raw = self._read(MASTER_CV_FILE)
        return MasterCV.from_dict(raw) if raw else None

    def save_master_cv(self, cv: MasterCV, commit_message: str = "Update master CV") -> None:
        self._write(MASTER_CV_FILE, cv.to_dict(), commit_message)

    def load_applications(self) -> list[Application]:
        raw = self._read(APPLICATIONS_FILE) or []
        return [Application.from_dict(a) for a in raw]

    def save_applications(self, apps: list[Application], commit_message: str = "Update applications tracker") -> None:
        self._write(APPLICATIONS_FILE, [a.to_dict() for a in apps], commit_message)

    def load_generated_versions(self) -> list[GeneratedVersion]:
        raw = self._read(GENERATED_VERSIONS_FILE) or []
        return [GeneratedVersion.from_dict(v) for v in raw]

    def save_generated_versions(self, versions: list[GeneratedVersion], commit_message: str = "Log generated version") -> None:
        self._write(GENERATED_VERSIONS_FILE, [v.to_dict() for v in versions], commit_message)

    # --- generated document files (CV/cover letter .docx per application) ---
    def save_generated_document(self, relative_path: str, content: bytes, commit_message: str = "") -> None:
        try:
            existing = self._repo.get_contents(relative_path, ref=self._branch)
            self._repo.update_file(relative_path, commit_message or f"Update {relative_path}", content, existing.sha, branch=self._branch)
        except Exception:
            self._repo.create_file(relative_path, commit_message or f"Add {relative_path}", content, branch=self._branch)


def get_storage():
    """Pick GitHub-backed storage when configured (cloud), else local files (dev)."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not (token and repo):
        try:
            import streamlit as st

            token = token or st.secrets.get("GITHUB_TOKEN")
            repo = repo or st.secrets.get("GITHUB_REPO")
        except Exception:
            pass

    if token and repo:
        branch = os.environ.get("GITHUB_BRANCH", "main")
        return GitHubYAMLStorage(token=token, repo_name=repo, branch=branch)
    return LocalYAMLStorage()
