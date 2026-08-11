"""
Unit tests for JWTAuthEngine and WorkspaceRBAC (EPIC G6-2).
"""


from ape.security.auth import JWTAuthEngine
from ape.security.rbac import WorkspaceRBAC


def test_jwt_auth_engine():
    engine = JWTAuthEngine(secret_key="my_test_secret_key")
    token = engine.create_token(sub="user_01", role="ADMIN", workspace_slug="prod_ws", ttl_seconds=10)

    assert isinstance(token, str)
    claims = engine.decode_token(token)

    assert claims is not None
    assert claims.sub == "user_01"
    assert claims.role == "ADMIN"
    assert claims.workspace_slug == "prod_ws"


def test_workspace_rbac():
    rbac = WorkspaceRBAC()

    assert rbac.check_permission("ADMIN", "write") is True
    assert rbac.check_permission("ADMIN", "release") is True
    assert rbac.check_permission("DEVELOPER", "write") is True
    assert rbac.check_permission("DEVELOPER", "release") is False
    assert rbac.check_permission("AUDITOR", "read") is True
    assert rbac.check_permission("AUDITOR", "write") is False
