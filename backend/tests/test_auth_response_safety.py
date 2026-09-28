from app.api.auth import current_user


def test_auth_me_returns_authenticated_identity_without_error_wrapping():
    user = {"sub": "fixture-user", "email": "fixture@example.invalid"}

    assert current_user(user) == {"authenticated": True, "user": user}


def test_auth_route_does_not_embed_exception_text_in_client_detail():
    source = __import__("inspect").getsource(current_user)

    assert "detail=f" not in source
    assert "str(" not in source
