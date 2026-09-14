"""Restore rehearsal for the fixed disposable Supabase container only.

No host backup file, remote connection or production option. Creates a fresh
database inside the local container. Retains it and the synthetic archive for
review; never drops a pre-existing database. This is not production backup tooling.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
from uuid import uuid4

CONTAINER="supabase_db_profit-radar-disposable"
LABEL="profit-radar-disposable"


def command(args):
    completed=subprocess.run(args,capture_output=True,text=True,timeout=180,check=False)
    if completed.returncode:
        raise RuntimeError("Isolated restore command failed; no raw database output recorded")
    return completed.stdout.strip()


def sql(db,query):
    if db!="postgres" and not re.fullmatch(r"pr_restore_[a-f0-9]{32}",db):
        raise ValueError("Invalid isolated database name")
    return command(["docker","exec",CONTAINER,"psql","-X","-h","/var/run/postgresql","-U","postgres","-d",db,"-v","ON_ERROR_STOP=1","-Atc",query])


def fingerprint(db):
    # Schema/ACL metadata stays in memory and is hashed, never printed. Customer
    # content is not read: row checks below use counts, NOT row values.
    parts=[]
    for query in (
        "select n.nspname,c.relname,c.relkind,c.relrowsecurity,c.relforcerowsecurity,c.relowner,c.relacl from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('public','auth') and c.relkind in ('r','v','S') order by 1,2",
        "select table_schema,table_name,column_name,data_type,is_nullable,column_default from information_schema.columns where table_schema in ('public','auth') order by 1,2,ordinal_position",
        "select schemaname,tablename,policyname,roles,cmd,qual,with_check from pg_policies where schemaname in ('public','auth') order by 1,2,3",
        "select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),p.proowner,p.proacl,p.prosecdef,p.proconfig,pg_get_functiondef(p.oid) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','auth') and p.prokind='f' order by 1,2,3",
        "select n.nspname,c.relname,a.attname,a.attacl from pg_attribute a join pg_class c on c.oid=a.attrelid join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('public','auth') and a.attnum>0 and not a.attisdropped order by 1,2,3",
        "select n.nspname,c.relname,con.conname,pg_get_constraintdef(con.oid) from pg_constraint con join pg_class c on c.oid=con.conrelid join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('public','auth') order by 1,2,3",
    ):
        parts.append(sql(db,query))
    tables=sql(db,"select quote_ident(schemaname)||'.'||quote_ident(tablename) from pg_tables where schemaname in ('public','auth') order by 1").splitlines()
    for table in tables:
        # Returned SQL identifiers are quoted by PostgreSQL, not caller input.
        parts.append(table+":"+sql(db,"select count(*) from "+table))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest(),len(tables)


def run(approved=False,workers_stopped=False):
    if not approved or not workers_stopped:raise ValueError("Explicit disposable fixture and stopped-writer approval required")
    if os.getenv("DOCKER_HOST") or os.getenv("DOCKER_CONTEXT"):
        raise ValueError("Docker endpoint overrides are not allowed")
    context=json.loads(command(["docker","context","inspect"]))[0]
    endpoint=context.get("Endpoints",{}).get("docker",{}).get("Host","")
    if not (endpoint.startswith("npipe://") or endpoint=="unix:///var/run/docker.sock"):
        raise ValueError("Local Docker engine required")
    info=json.loads(command(["docker","inspect",CONTAINER]))[0]
    labels=info.get("Config",{}).get("Labels",{}) or {}
    if labels.get("com.supabase.cli.project")!=LABEL or not info.get("State",{}).get("Running"):
        raise ValueError("Disposable container identity mismatch")
    ports=info.get("NetworkSettings",{}).get("Ports",{}).get("5432/tcp",[]) or []
    if not ports or any(p.get("HostPort")!="54322" or p.get("HostIp") not in {"127.0.0.1","::1","0.0.0.0","::"} for p in ports):
        raise ValueError("Unexpected disposable database port")
    database="pr_restore_"+uuid4().hex
    folder="/tmp/"+database
    archive=folder+"/synthetic.dump"
    before,count=fingerprint("postgres")
    command(["docker","exec",CONTAINER,"install","-d","-m","700",folder])
    command(["docker","exec",CONTAINER,"pg_dump","-h","/var/run/postgresql","-U","postgres","-d","postgres","-Fc","-n","public","-n","auth","-n","extensions","-e","uuid-ossp","-e","pgcrypto","-f",archive])
    command(["docker","exec",CONTAINER,"createdb","-h","/var/run/postgresql","-U","postgres","-T","template0",database])
    # Only the newly created random target is cleaned, never the source DB.
    command(["docker","exec",CONTAINER,"pg_restore","-h","/var/run/postgresql","-U","postgres","-d",database,"--single-transaction","--exit-on-error","--clean","--if-exists",archive])
    restored,restored_count=fingerprint(database)
    after,_=fingerprint("postgres")
    if before!=after:raise RuntimeError("Source changed during rehearsal; stop writers and repeat with a fresh target")
    if restored!=before or restored_count!=count:raise RuntimeError("Restore metadata/count verification failed; retain target for review")
    return {"restore_verified":True,"source_unchanged":True,"table_count":count,"target_database":database,
            "retained_archive":archive,"scope":"public/auth schema, ACL and row counts; not full Supabase disaster recovery"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-disposable-fixtures",action="store_true")
    parser.add_argument("--workers-stopped",action="store_true")
    args=parser.parse_args()
    print(json.dumps(run(args.allow_disposable_fixtures,args.workers_stopped)))


if __name__=="__main__":
    try:main()
    except Exception:
        print('{"restore_verified":false,"error":"ISOLATED_RESTORE_NOT_COMPLETED"}')
        raise SystemExit(1) from None
