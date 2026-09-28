"""Create an encrypted logical backup using pg_dump and age.

Connection settings and the age identity are injected by the server-side secret
store. They never appear in argv, logs or the manifest. This command is not
enabled by repository deployment templates until the owner selects storage.
"""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from uuid import uuid4


class BackupError(RuntimeError):
    pass


def configuration(repo=None):
    names = ("PGHOST", "PGPORT", "PGUSER", "PGDATABASE", "PGPASSWORD",
             "BACKUP_DIR", "BACKUP_AGE_RECIPIENT", "BACKUP_AGE_IDENTITY_FILE",
             "BACKUP_RETENTION_DAYS")
    if any(not os.getenv(name, "").strip() for name in names):
        raise BackupError("Backup configuration incomplete")
    host = os.environ["PGHOST"].strip().lower()
    environment = os.getenv("APP_ENV", "").strip().lower()
    if environment not in {"test", "staging", "production"}:
        raise BackupError("Backup environment invalid")
    if environment == "production" and (host in {"localhost", "127.0.0.1", "::1"}
                                         or os.getenv("PGSSLMODE") != "verify-full"):
        raise BackupError("Production backup connection must be remote TLS verified")
    if not re.fullmatch(r"age1[0-9a-z]{20,100}", os.environ["BACKUP_AGE_RECIPIENT"]):
        raise BackupError("Backup encryption recipient invalid")
    try:
        retention = int(os.environ["BACKUP_RETENTION_DAYS"])
        port = int(os.environ["PGPORT"])
    except ValueError:
        raise BackupError("Backup numeric configuration invalid") from None
    if not 1 <= retention <= 3650 or not 1 <= port <= 65535:
        raise BackupError("Backup numeric configuration invalid")
    target = Path(os.environ["BACKUP_DIR"]).resolve()
    identity = Path(os.environ["BACKUP_AGE_IDENTITY_FILE"]).resolve()
    repository = Path(repo or Path(__file__).resolve().parents[2]).resolve()
    if target == repository or repository in target.parents or identity == repository or repository in identity.parents:
        raise BackupError("Backup material must remain outside the repository")
    if not identity.is_file():
        raise BackupError("Backup restore identity unavailable")
    if not shutil.which("pg_dump") or not shutil.which("pg_restore") or not shutil.which("age"):
        raise BackupError("Backup tools unavailable")
    return target, identity, retention


def create_backup():
    target, identity, retention = configuration()
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc)
    artifact = target / f"profit-radar-{stamp:%Y%m%dT%H%M%SZ}-{uuid4().hex}.dump.age"
    partial = artifact.with_suffix(artifact.suffix + ".partial")
    child_env = dict(os.environ)
    try:
        with partial.open("xb") as encrypted:
            dump = subprocess.Popen(["pg_dump", "-w", "-Fc", "--blobs"], stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, env=child_env)
            age = subprocess.Popen(["age", "-r", os.environ["BACKUP_AGE_RECIPIENT"]],
                                   stdin=dump.stdout, stdout=encrypted, stderr=subprocess.DEVNULL)
            dump.stdout.close()
            age_code = age.wait(timeout=1800)
            dump_code = dump.wait(timeout=1800)
        if dump_code or age_code or partial.stat().st_size < 1024:
            raise BackupError("Encrypted backup creation failed")
        # Verify decryption and pg_restore catalog parsing without exposing rows.
        decrypt = subprocess.Popen(["age", "-d", "-i", str(identity), str(partial)],
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        listing = subprocess.run(["pg_restore", "--list"], stdin=decrypt.stdout,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 timeout=300, check=False)
        decrypt.stdout.close()
        if listing.returncode or decrypt.wait(timeout=30):
            raise BackupError("Encrypted backup verification failed")
        partial.replace(artifact)
    except Exception:
        if partial.exists():
            partial.unlink()
        raise
    with artifact.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest().upper()
    manifest = artifact.with_suffix(artifact.suffix + ".manifest.json")
    manifest.write_text(json.dumps({"artifact": artifact.name, "sha256": digest,
        "completed_at": stamp.isoformat(timespec="seconds"), "encrypted": True,
        "catalog_verified": True}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    cutoff = stamp - timedelta(days=retention)
    for old in target.glob("profit-radar-*.dump.age"):
        if old != artifact and datetime.fromtimestamp(old.stat().st_mtime, timezone.utc) < cutoff:
            old.unlink()
            old.with_suffix(old.suffix + ".manifest.json").unlink(missing_ok=True)
    return {"event": "encrypted_backup_completed", "severity": "info",
            "completed_at": stamp.isoformat(timespec="seconds"), "sha256": digest,
            "catalog_verified": True}


def main():
    try:
        print(json.dumps(create_backup(), sort_keys=True))
    except Exception:
        print('{"event":"encrypted_backup_failed","severity":"critical"}')
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
