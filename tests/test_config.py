import pytest
from pydantic import ValidationError
import os

def test_config_validation():
    from config import Settings

    # Valid Case
    os.environ['OPENROUTER_KEY'] = 'sk-test'
    settings = Settings()
    assert settings.OPENROUTER_KEY.get_secret_value() == 'sk-test'
    assert settings.IB_PORT == 7497

def test_config_dashboard_auth():
    from config import Settings
    os.environ['DASHBOARD_USERNAME'] = 'admin'
    os.environ['DASHBOARD_PASSWORD'] = 'secret'
    os.environ['OPENROUTER_KEY'] = 'sk-test'

    settings = Settings()
    assert settings.DASHBOARD_USERNAME == 'admin'
    assert settings.DASHBOARD_PASSWORD.get_secret_value() == 'secret'

def test_config_missing_required():
    from config import Settings
    from unittest.mock import patch

    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValidationError):
            Settings()

def test_config_global_exception_handling():
    import builtins
    import importlib
    import config
    from unittest.mock import patch

    # We want to force the `Config = Settings()` in config.py to fail and hit the except block.
    # We can do this by temporarily removing the environment variable and re-importing the module.
    with patch.dict('os.environ', {}, clear=True):
        importlib.reload(config)
        assert config.Config is None

    # Restore configuration for other tests that might need it
    importlib.reload(config)
