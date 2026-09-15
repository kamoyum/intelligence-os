from pathlib import Path

from intelligence_os.security import ensure_api_token


def test_token_is_persistent(tmp_path: Path):
    p = tmp_path / "token.txt"
    a = ensure_api_token(p)
    b = ensure_api_token(p)
    assert a == b
    assert len(a) >= 32
