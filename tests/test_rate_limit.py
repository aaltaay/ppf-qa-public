from backend import rate_limit


def test_rate_limit_allows_first_request():
    rate_limit._rate_limits.clear()
    assert rate_limit.check_rate_limit("pytest-smoke-ip") is True
