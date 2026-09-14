from argparse import Namespace
from uuid import uuid4
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location("recovery",Path(__file__).resolve().parents[1]/"scripts/recover_company_work.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_recovery_needs_exact_target_and_worker_attestation(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL","http://127.0.0.1:54321")
    args=Namespace(company=str(uuid4()),expected_url="https://other.invalid",apply=False,owner=None)
    with pytest.raises(ValueError,match="Target mismatch"):module.validate(args)
    args.expected_url="http://127.0.0.1:54321";args.apply=True;args.workers_stopped=False
    with pytest.raises(ValueError,match="attestation"):module.validate(args)
    args.workers_stopped=True;args.owner=str(uuid4());args.operator="operator1";args.ticket="incident1"
    module.validate(args)
