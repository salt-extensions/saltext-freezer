import logging
import os

import pytest
from saltext.freezer import PACKAGE_ROOT
from saltfactories.utils import random_string


# Reset the root logger to its default level(because salt changed it)
logging.root.setLevel(logging.WARNING)


# This swallows all logging to stdout.
# To show select logs, set --log-cli-level=<level>
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
    handler.close()


@pytest.fixture(scope="session")
def salt_factories_config():
    """
    Return a dictionary with the keyword arguments for FactoriesManager
    """
    return {
        "code_dir": str(PACKAGE_ROOT),
        "inject_sitecustomize": "COVERAGE_PROCESS_START" in os.environ,
        "start_timeout": 120 if os.environ.get("CI") else 60,
    }


@pytest.fixture
def temp_salt_master(
    request,
    salt_factories,
):
    config_defaults = {
        "open_mode": True,
    }
    factory = salt_factories.salt_master_daemon(
        random_string("temp-master-"),
        defaults=config_defaults,
        extra_cli_arguments_after_first_start_failure=["--log-level=info"],
    )
    return factory


@pytest.fixture
def temp_salt_minion(temp_salt_master):
    config_defaults = {
        "open_mode": True,
    }
    factory = temp_salt_master.salt_minion_daemon(
        random_string("temp-minion-"),
        defaults=config_defaults,
        extra_cli_arguments_after_first_start_failure=["--log-level=info"],
    )
    factory.after_terminate(pytest.helpers.remove_stale_minion_key, temp_salt_master, factory.id)
    return factory


@pytest.fixture(scope="package")
def master(salt_factories):
    return salt_factories.salt_master_daemon(random_string("master-"))


@pytest.fixture(scope="package")
def minion(master):
    return master.salt_minion_daemon(random_string("minion-"))
