"""Actual GoTrue login + fresh PostgREST against the v2 synthetic database.

No custom-minted user JWT, no auth verification bypass. Local keys remain in memory.
Retains fixture users/DB and a uniquely named loopback-only PostgREST container.
"""
import json
import os
import secrets
import subprocess
import time
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4
import httpx
from supabase import create_client
from validate_forward_local import command, sql, rows_fingerprint
from run_local_regression import local_credentials


def verify(db):
    keys = local_credentials()
    info = json.loads(command(['docker', 'inspect', 'supabase_rest_profit-radar-disposable']))[0]
    if info['Config']['Labels'].get('com.supabase.cli.project') != 'profit-radar-disposable':
        raise ValueError('Unexpected local PostgREST')
    settings = dict(x.split('=', 1) for x in info['Config']['Env'])
    uri = urlsplit(settings['PGRST_DB_URI'])
    if not uri.hostname.startswith('supabase_db_'):
        raise ValueError('Local database host required')
    settings['PGRST_DB_URI'] = urlunsplit((uri.scheme, uri.netloc, '/' + db, uri.query, ''))
    settings['PGRST_DB_SCHEMAS'] = 'public'
    settings['PGRST_DB_EXTRA_SEARCH_PATH'] = 'public,pg_catalog'
    name = 'pr-forward-rest-' + uuid4().hex
    args = ['docker', 'run', '-d', '--name', name, '--network', next(iter(info['NetworkSettings']['Networks'])),
            '-p', '127.0.0.1::3000']
    for key in settings:
        if key.startswith('PGRST_'):
            args += ['--env', key]
    result = subprocess.run(args + [info['Config']['Image']], env=dict(os.environ, **settings), capture_output=True)
    if result.returncode:
        raise RuntimeError('Synthetic PostgREST startup failed')
    started = json.loads(command(['docker', 'inspect', name]))[0]
    port = started['NetworkSettings']['Ports']['3000/tcp'][0]['HostPort']
    base = 'http://127.0.0.1:' + port
    with httpx.Client(base_url=base, timeout=15) as client:
        for _ in range(30):
            try:
                if client.get('/').status_code == 200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(.2)
        else:
            raise RuntimeError('Synthetic PostgREST not ready')
        admin = create_client('http://127.0.0.1:54321', keys['service_role'])
        browser = create_client('http://127.0.0.1:54321', keys['anon'])
        email, password = 'v2-' + uuid4().hex + '@example.invalid', secrets.token_urlsafe(32)
        user = admin.auth.admin.create_user({'email': email, 'password': password, 'email_confirm': True}).user
        token = browser.auth.sign_in_with_password({'email': email, 'password': password}).session.access_token
        sql(db, f"insert into auth.users(id,email) values('{user.id}','{email}');")
        body = {'p_user_id': user.id, 'p_company_name': 'V2 JWT fixture', 'p_name': 'Synthetic', 'p_email': email}
        before = rows_fingerprint(db, ['companies', 'profiles'])
        for credential in (keys['anon'], token):
            r = client.post('/rpc/onboard_user', headers={'Authorization': 'Bearer ' + credential}, json=body)
            assert r.status_code in (401, 403) and r.json()['code'] == '42501'
        assert before == rows_fingerprint(db, ['companies', 'profiles'])
        r = client.post('/rpc/create_company_and_profile', headers={'Authorization': 'Bearer ' + token},
                        json={'company_name': 'V2 JWT fixture', 'owner_name': 'Synthetic'})
        assert r.status_code == 200, 'Canonical legitimate JWT registration failed'
        company = r.json()
        assert sql(db, f"select count(*) from public.profiles where user_id='{user.id}' and company_id='{company}' and role='owner';") == '1'
        after = rows_fingerprint(db, ['companies', 'profiles'])
        r = client.post('/rpc/create_company_and_profile', headers={'Authorization': 'Bearer ' + token},
                        json={'company_name': 'V2 duplicate', 'owner_name': 'Synthetic'})
        assert r.status_code == 400 and r.json()['code'] == 'P0001'
        assert after == rows_fingerprint(db, ['companies', 'profiles'])
        r = client.post('/rpc/onboard_user', headers={'Authorization': 'Bearer ' + keys['service_role']}, json=body)
        assert r.status_code == 200 and r.json()['created'] is False
        assert after == rows_fingerprint(db, ['companies', 'profiles'])
        for credential in (keys['anon'], keys['service_role']):
            r = client.post('/rpc/create_company_and_profile', headers={'Authorization': 'Bearer ' + credential},
                            json={'company_name': 'Forbidden', 'owner_name': 'Forbidden'})
            assert r.status_code in (401, 403) and r.json()['code'] == '42501'
        for table in ('billing_checkout_attempts', 'gmail_sync_cursors', 'ai_budget_reservations'):
            r = client.get('/' + table, headers={'Authorization': 'Bearer ' + token})
            assert r.status_code == 403 and r.json()['code'] == '42501'
        email2 = 'v2-' + uuid4().hex + '@example.invalid'
        user2 = admin.auth.admin.create_user({'email': email2, 'password': secrets.token_urlsafe(32), 'email_confirm': True}).user
        sql(db, f"insert into auth.users(id,email) values('{user2.id}','{email2}');")
        body2 = dict(body, p_user_id=user2.id, p_email=email2)
        r = client.post('/rpc/onboard_user', headers={'Authorization': 'Bearer ' + keys['service_role']}, json=body2)
        assert r.status_code == 200 and r.json()['created'] is True
        assert sql(db, f"select count(*) from public.profiles where user_id='{user2.id}';") == '1'
    return {'real_local_jwt': True, 'legacy_browser_denied': True, 'canonical_registration': True,
            'duplicate_safe': True, 'service_existing_profile': True, 'service_new_profile': True,
            'internal_tables_denied': True, 'retained_rest_container': name}
