import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "build_release_artifact.py"
SPEC = importlib.util.spec_from_file_location("build_release_artifact", SCRIPT)
artifact_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artifact_builder)


def command(directory, *args):
    subprocess.run(["git", *args], cwd=directory, capture_output=True, check=True)


def repository(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    command(repo, "init")
    command(repo, "config", "user.email", "release@example.invalid")
    command(repo, "config", "user.name", "Release Test")
    (repo / "file.txt").write_text("release\n", encoding="utf-8")
    command(repo, "add", "file.txt")
    command(repo, "commit", "-m", "release")
    return repo


def test_release_artifact_is_commit_addressed_and_hashed(tmp_path):
    repo = repository(tmp_path)
    artifact, manifest_path, manifest = artifact_builder.build(repo, tmp_path / "out")
    assert artifact.is_file() and manifest_path.is_file()
    assert manifest["commit"] in artifact.name
    assert len(manifest["sha256"]) == 64
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["source_tree"] == "clean"


def test_release_artifact_rejects_dirty_or_in_repo_output(tmp_path):
    repo = repository(tmp_path)
    (repo / "dirty.txt").write_text("not reviewed", encoding="utf-8")
    with pytest.raises(RuntimeError, match="clean reviewed"):
        artifact_builder.build(repo, tmp_path / "out")
    command(repo, "add", "dirty.txt")
    command(repo, "commit", "-m", "dirty now reviewed")
    with pytest.raises(RuntimeError, match="outside"):
        artifact_builder.build(repo, repo / "artifacts")
