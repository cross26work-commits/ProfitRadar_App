"""Dedicated scheduler process, not a browser session. No automatic registration.

Run under a process supervisor after explicit deployment approval.
One HTTP attempt each five minutes; DB company locks prevent overlaps.
"""
import os,time,json
from urllib.parse import urlsplit
import requests


def tick():
    base=os.getenv("SCHEDULER_BACKEND_URL", "").rstrip("/")
    secret=os.getenv("GMAIL_SCHEDULER_SECRET", "")
    target=urlsplit(base)
    if (not secret or target.username or target.password or target.query or target.fragment
            or target.path not in {"","/"} or not target.hostname
            or (target.scheme!="https" and not(target.scheme=="http" and target.hostname in {"localhost","127.0.0.1"}))):
        raise RuntimeError("Invalid scheduler configuration")
    try:
        result=requests.post(base+"/gmail/scheduled-sync",headers={"X-Scheduler-Secret":secret},timeout=60,allow_redirects=False)
        result.raise_for_status()
        body=result.json()
        print(json.dumps({"event":"sync_batch",**{key:body.get(key) for key in ("processed","succeeded","failed","busy")}}),flush=True)
    except Exception:
        print('{"event":"sync_batch_failed"}',flush=True)


def main():
    while True:
        started=time.monotonic()
        tick()
        time.sleep(max(1,300-(time.monotonic()-started)))


if __name__=="__main__": main()
