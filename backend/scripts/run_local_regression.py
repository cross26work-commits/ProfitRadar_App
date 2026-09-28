"""Explicit local Docker fixture regression. Credentials stay in process memory."""
import argparse
import json
import os
import re
import subprocess
import sys
import jwt
from validate_forward_local import validate_target, command, ROOT


def local_credentials():
    info = json.loads(command(['docker', 'inspect', 'supabase_kong_profit-radar-disposable']))[0]
    if info['Config']['Labels'].get('com.supabase.cli.project') != 'profit-radar-disposable':
        raise ValueError('Unexpected gateway')
    env = dict(x.split('=', 1) for x in info['Config']['Env'])
    content = command(['docker', 'exec', 'supabase_kong_profit-radar-disposable', 'cat', env['KONG_DECLARATIVE_CONFIG']])
    keys = {}
    for candidate in re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', content):
        role = jwt.decode(candidate, options={'verify_signature': False}).get('role')
        if role in {'anon', 'service_role'}:
            keys[role] = candidate
    if set(keys) != {'anon', 'service_role'}:
        raise ValueError('Local gateway credentials unavailable')
    return keys


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-disposable-fixtures', action='store_true')
    args = parser.parse_args()
    validate_target(args.allow_disposable_fixtures)
    keys = local_credentials()
    env = dict(os.environ, P0_SUPABASE_TEST_URL='http://127.0.0.1:54321',
               P0_SUPABASE_EXPECTED_URL='http://127.0.0.1:54321', P0_ALLOW_FIXTURE_WRITES='CREATE_DISPOSABLE_FIXTURES',
               P0_SUPABASE_TEST_ANON_KEY=keys['anon'], P0_SUPABASE_TEST_SERVICE_KEY=keys['service_role'],
               FINAL_GATE_LOCAL_TEST='allow-disposable-fixtures',
               PR_AUTH_E2E_LOCAL_TEST='ALLOW_DISPOSABLE_LOCAL')
    for selection in (['tests/integration'], []):
        result = subprocess.run([sys.executable, '-m', 'pytest', *selection, '-q', '-rs', '--tb=short'],
                                cwd=ROOT / 'backend', env=env)
        if result.returncode:
            raise SystemExit(result.returncode)
