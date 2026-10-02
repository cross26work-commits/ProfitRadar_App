"""Global test isolation applied before application modules import dotenv files.

The developer's ignored ``backend/.env`` may contain a real project URL. Unit
tests must never inherit it. Integration fixtures explicitly replace these
loopback values with their separately validated disposable target.
"""
import os


os.environ["APP_ENV"] = "test"
os.environ["SUPABASE_URL"] = os.getenv("P0_SUPABASE_TEST_URL", "http://127.0.0.1:54321")
os.environ["SUPABASE_ANON_KEY"] = os.getenv("P0_SUPABASE_TEST_ANON_KEY", "synthetic-test-anon")
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.getenv("P0_SUPABASE_TEST_SERVICE_KEY", "synthetic-test-service")
os.environ["SUPABASE_JWT_SECRET"] = "synthetic-test-jwt-secret-at-least-32-characters"
