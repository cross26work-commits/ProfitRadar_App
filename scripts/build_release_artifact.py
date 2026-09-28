"""Create a content-addressed release source artifact from a clean Git commit."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def git(repo, *args):
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                            encoding="utf-8", check=False)
    if result.returncode:
        raise RuntimeError("Release Git inspection failed")
    return result.stdout.strip()


def build(repo, output_dir):
    repo = Path(repo).resolve()
    output_dir = Path(output_dir).resolve()
    if repo == output_dir or repo in output_dir.parents:
        raise RuntimeError("Release artifacts must be written outside the repository")
    if git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("Release artifact requires a clean reviewed working tree")
    commit = git(repo, "rev-parse", "HEAD")
    if len(commit) != 40:
        raise RuntimeError("Release commit identity unavailable")
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / f"profit-radar-{commit}.tar.gz"
    completed = subprocess.run(["git", "archive", "--format=tar.gz", f"--output={artifact}", commit],
                               cwd=repo, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError("Release artifact creation failed")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest().upper()
    manifest = {
        "artifact": artifact.name, "commit": commit, "sha256": digest,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_tree": "clean", "format": "git-archive-tar-gzip",
    }
    manifest_path = artifact.with_suffix(artifact.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact, manifest_path, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    _, manifest_path, manifest = build(args.repo, args.output_dir)
    print(json.dumps({"manifest": str(manifest_path), "commit": manifest["commit"],
                      "sha256": manifest["sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
