"""Create a production pg_dump archive and prove it restores to a NEW local DB.

Run interactively on the owner's computer. The database password is read from
the terminal, never from argv, an environment variable, a file, or the report.
This script does not run migrations and never writes to the remote database.
"""

import argparse
import csv
import getpass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4


PROJECT_ID = "zszmetqhksthduoxfvac"
CONTAINER = "supabase_db_profit-radar-disposable"
LABEL = "profit-radar-disposable"
IMAGE = "public.ecr.aws/supabase/postgres:17.6.1.167"
DEFAULT_BACKUP_DIR = Path.home() / "ProfitRadar_production_backups"


class BackupError(Exception):
    pass


def run_safe(args, *, timeout=120, input_bytes=None):
    result = subprocess.run(args, input=input_bytes, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout, check=False)
    if result.returncode:
        # Native error text can contain connection metadata. Do not echo it.
        raise BackupError(f"Local operation failed: {args[0]} (exit {result.returncode})")
    return result.stdout


def assert_disposable_container():
    if os.getenv("DOCKER_HOST") or os.getenv("DOCKER_CONTEXT"):
        raise BackupError("Docker endpoint override is forbidden")
    context = json.loads(run_safe(["docker", "context", "inspect"]))[0]
    endpoint = context.get("Endpoints", {}).get("docker", {}).get("Host", "")
    if not (endpoint.startswith("npipe://") or endpoint == "unix:///var/run/docker.sock"):
        raise BackupError("A local Docker engine is required")
    info = json.loads(run_safe(["docker", "inspect", CONTAINER]))[0]
    if not info.get("State", {}).get("Running") or \
            (info.get("Config", {}).get("Labels") or {}).get("com.supabase.cli.project") != LABEL or \
            info.get("Config", {}).get("Image") != IMAGE:
        raise BackupError("Disposable Supabase container identity mismatch")
    version = run_safe(["docker", "exec", CONTAINER, "pg_dump", "--version"]).decode("ascii", "replace")
    if "pg_dump (PostgreSQL) 17." not in version:
        raise BackupError("Expected PostgreSQL 17 pg_dump")


def source_identity(host, user, port, dbname):
    direct = host == f"db.{PROJECT_ID}.supabase.co" and user == "postgres" and port == 5432
    pooler = (host.endswith(".pooler.supabase.com") and
              user == f"postgres.{PROJECT_ID}" and port == 5432)
    if not (direct or pooler) or dbname != "postgres":
        raise BackupError("Source connection does not match the approved project identity")
    if not re.fullmatch(r"[a-z0-9.-]+", host):
        raise BackupError("Invalid source host")


def restrict_directory(path):
    if path.is_symlink():
        raise BackupError("Backup destination cannot be a symlink")
    if path.exists() and not path.is_dir():
        raise BackupError("Backup destination is not a directory")
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        path.chmod(0o700)
        return
    identity = run_safe(["whoami", "/user", "/fo", "csv", "/nh"]).decode("utf-8-sig", "replace")
    rows = list(csv.reader(io.StringIO(identity)))
    if len(rows) != 1 or len(rows[0]) != 2 or not re.fullmatch(r"S-1-5-[0-9-]+", rows[0][1]):
        raise BackupError("Cannot determine current Windows SID")
    sid = rows[0][1]
    run_safe(["icacls", str(path), "/inheritance:r", "/grant:r", f"*{sid}:(OI)(CI)F",
              "/grant:r", "*S-1-5-18:(OI)(CI)F"])


def dump_to_file(host, port, user, dbname, password, archive):
    # The password crosses only the Docker stdin pipe. It is absent from argv,
    # docker inspect, host environment, shell history, and our output.
    shell = ('IFS= read -r PGPASSWORD || exit 64; '
             'export PGPASSWORD PGSSLMODE=verify-full PGSSLROOTCERT=system; '
             'exec pg_dump -w -Fc --blobs -h "$1" -p "$2" -U "$3" -d "$4"')
    args = ["docker", "exec", "-i", CONTAINER, "sh", "-c", shell, "--",
            host, str(port), user, dbname]
    with archive.open("xb") as target:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=target,
                                stderr=subprocess.PIPE)
        try:
            _, stderr = proc.communicate((password + "\n").encode("utf-8"), timeout=1800)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise BackupError("pg_dump timed out") from None
    if proc.returncode:
        # Deliberately do not print provider error detail or the password.
        raise BackupError(f"pg_dump failed (exit {proc.returncode})")
    if archive.stat().st_size < 1024:
        raise BackupError("pg_dump archive is unexpectedly small")
    # Validate the archive structure without exposing its table contents.
    with archive.open("rb") as source:
        result = subprocess.run(["docker", "exec", "-i", CONTAINER, "pg_restore", "--list"],
                                stdin=source, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=300, check=False)
    if result.returncode:
        raise BackupError("pg_dump archive validation failed")


def restore_archive(archive):
    database = "pr_prodrestore_" + uuid4().hex
    remote_archive = "/tmp/" + database + ".dump"
    # Target name is generated here; it cannot name an existing source DB.
    run_safe(["docker", "exec", CONTAINER, "createdb", "-h", "/var/run/postgresql",
              "-U", "postgres", "-T", "template0", database])
    try:
        # template0 contains public; Supabase archives also create it. This
        # affects only the newly generated disposable target database.
        run_safe(["docker", "exec", CONTAINER, "psql", "-X", "-h",
                  "/var/run/postgresql", "-U", "postgres", "-d", database,
                  "-v", "ON_ERROR_STOP=1", "-c", "drop schema public cascade"])
        run_safe(["docker", "cp", str(archive), f"{CONTAINER}:{remote_archive}"], timeout=300)
        # Restore into the fresh database only. Never use --clean against source.
        run_safe(["docker", "exec", CONTAINER, "pg_restore", "-h", "/var/run/postgresql",
                  "-U", "supabase_admin", "-d", database, "--single-transaction",
                  "--exit-on-error", remote_archive], timeout=1800)
        # A successful pg_restore exit plus a live catalog query proves the
        # archive was accepted; no customer rows are read or printed.
        count = run_safe(["docker", "exec", CONTAINER, "psql", "-X", "-h",
                          "/var/run/postgresql", "-U", "postgres", "-d", database,
                          "-v", "ON_ERROR_STOP=1", "-Atc",
                          "select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                          "where n.nspname='public' and c.relkind='r'"]).strip()
        if not count.isdigit() or int(count) == 0:
            raise BackupError("Restored database has no public tables")
    finally:
        # This is an exact file inside the disposable container, not source data.
        run_safe(["docker", "exec", CONTAINER, "rm", "-f", remote_archive])
    return database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=f"db.{PROJECT_ID}.supabase.co")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--dbname", default="postgres")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    args = parser.parse_args()
    source_identity(args.host, args.user, args.port, args.dbname)
    repository = Path(__file__).resolve().parents[2]
    destination = args.backup_dir.resolve()
    if destination == repository or repository in destination.parents:
        raise BackupError("Backup destination must be outside the repository")
    assert_disposable_container()
    restrict_directory(args.backup_dir)
    archive = args.backup_dir / (f"{PROJECT_ID}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_"
                                 f"{uuid4().hex}.dump")
    if not sys.stdin.isatty():
        raise BackupError("Interactive local terminal required for hidden password input")
    password = getpass.getpass("Production PostgreSQL password (input hidden): ")
    if not password or "\n" in password or "\r" in password:
        raise BackupError("Invalid password input")
    try:
        dump_to_file(args.host, args.port, args.user, args.dbname, password, archive)
    except Exception:
        if archive.exists():
            archive.unlink()  # Only this incomplete, newly generated artifact.
        raise
    finally:
        password = ""
    completed = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest().upper()
    try:
        restore_archive(archive)
        result = "PASS"
    except Exception:
        # Retain the completed backup for recovery even if rehearsal fails.
        result = "FAIL"
    print(json.dumps({"backup_completion_utc": completed, "backup_artifact_path": str(archive),
                      "backup_sha256": digest, "restore_verification": result}, ensure_ascii=False))
    if result != "PASS":
        raise BackupError("Restore verification failed; completed backup retained")


if __name__ == "__main__":
    try:
        main()
    except (BackupError, OSError, subprocess.TimeoutExpired):
        print("Backup/restore proof incomplete; v2 migration remains prohibited.", file=sys.stderr)
        raise SystemExit(1) from None
