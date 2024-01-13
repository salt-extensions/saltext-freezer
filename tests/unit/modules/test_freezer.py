"""
:maintainer:    Alberto Planas <aplanas@suse.com>
:platform:      Linux
"""
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import salt.modules.freezer as freezer
from salt.exceptions import CommandExecutionError


@pytest.fixture
def configure_loader_modules():
    return {freezer: {"__salt__": {}, "__opts__": {"cachedir": ""}}}


def test_status():
    """
    Test if a frozen state exist.
    """
    with patch("os.path.isfile", MagicMock(side_effect=[True, True])):
        assert freezer.status()

    with patch("os.path.isfile", MagicMock(side_effect=[True, False])):
        assert not freezer.status()


def test_list():
    """
    Test the listing of all frozen states.
    """
    # There is no freezer directory
    with patch("os.path.isdir", MagicMock(return_value=False)):
        assert freezer.list_() == []

    # There is freezer directory, but is empty
    with patch("os.path.isdir", MagicMock(return_value=True)), patch(
        "os.listdir", MagicMock(return_value=[])
    ):
        assert freezer.list_() == []

    # There is freezer directory with states
    with patch("os.path.isdir", MagicMock(return_value=True)), patch(
        "os.listdir",
        MagicMock(
            return_value=[
                "freezer-pkgs.yml",
                "freezer-reps.yml",
                "state-pkgs.yml",
                "state-reps.yml",
                "random-file",
            ]
        ),
    ):
        assert freezer.list_() == ["freezer", "state"]


def test_freeze_fails_cache():
    """
    Test to freeze a current installation
    """
    # Fails when creating the freeze cache directory
    with patch("os.makedirs", MagicMock(side_effect=OSError())):
        with pytest.raises(CommandExecutionError):
            freezer.freeze()


def test_freeze_fails_already_frozen():
    """
    Test to freeze a current installation
    """
    # Fails when there is already a frozen state
    makedirs = MagicMock()
    with patch("salt.modules.freezer.status", MagicMock(return_value=True)), patch(
        "os.makedirs", makedirs
    ):
        with pytest.raises(CommandExecutionError):
            freezer.freeze()
    makedirs.assert_called_once()


def test_freeze_success_two_freeze():
    """
    Test to freeze a current installation
    """
    # Freeze the current new state
    salt_mock = {
        "pkg.list_pkgs": MagicMock(return_value={}),
        "pkg.list_repos": MagicMock(return_value={}),
    }
    fopen = MagicMock()
    dump = MagicMock()
    makedirs = MagicMock()
    with patch.dict(freezer.__salt__, salt_mock), patch(
        "salt.modules.freezer.status",
        MagicMock(return_value=False),
    ), patch("salt.utils.json.dump", dump), patch("salt.modules.freezer.fopen", fopen,), patch(
        "os.makedirs", makedirs
    ):
        assert freezer.freeze("one")
        assert freezer.freeze("two")

        assert makedirs.call_count == 2
        assert salt_mock["pkg.list_pkgs"].call_count == 2
        assert salt_mock["pkg.list_repos"].call_count == 2
        fopen.assert_called()
        dump.assert_called()


def test_freeze_success_new_state():
    """
    Test to freeze a current installation
    """
    # Freeze the current new state
    salt_mock = {
        "pkg.list_pkgs": MagicMock(return_value={}),
        "pkg.list_repos": MagicMock(return_value={}),
    }
    fopen = MagicMock()
    dump = MagicMock()
    makedirs = MagicMock()
    with patch.dict(freezer.__salt__, salt_mock), patch(
        "salt.modules.freezer.status",
        MagicMock(return_value=False),
    ), patch("salt.utils.json.dump", dump), patch("salt.modules.freezer.fopen", fopen,), patch(
        "os.makedirs", makedirs
    ):
        assert freezer.freeze()
        makedirs.assert_called_once()
        salt_mock["pkg.list_pkgs"].assert_called_once()
        salt_mock["pkg.list_repos"].assert_called_once()
        fopen.assert_called()
        dump.assert_called()


def test_freeze_success_force():
    """
    Test to freeze a current installation
    """
    # Freeze the current old state
    salt_mock = {
        "pkg.list_pkgs": MagicMock(return_value={}),
        "pkg.list_repos": MagicMock(return_value={}),
    }
    fopen = MagicMock()
    dump = MagicMock()
    makedirs = MagicMock()
    with patch.dict(freezer.__salt__, salt_mock), patch(
        "salt.modules.freezer.status",
        MagicMock(return_value=False),
    ), patch("salt.utils.json.dump", dump), patch("salt.modules.freezer.fopen", fopen,), patch(
        "os.makedirs", makedirs
    ):
        assert freezer.freeze(force=True)
        makedirs.assert_called_once()
        salt_mock["pkg.list_pkgs"].assert_called_once()
        salt_mock["pkg.list_repos"].assert_called_once()
        fopen.assert_called()
        dump.assert_called()


def test_restore_fails_missing_state():
    """
    Test to restore an old state
    """
    # Fails if the state is not found
    with patch("salt.modules.freezer.status", MagicMock(return_value=False)):
        with pytest.raises(CommandExecutionError):
            freezer.restore()


def test_restore_add_missing_repo():
    """
    Test to restore an old state
    """
    # Only a missing repo is installed
    salt_mock = {
        "pkg.list_pkgs": MagicMock(return_value={}),
        "pkg.list_repos": MagicMock(return_value={}),
        "pkg.mod_repo": MagicMock(),
    }
    fopen = MagicMock()
    load = MagicMock(side_effect=[{}, {"missing-repo": {}}])
    with patch.dict(freezer.__salt__, salt_mock), patch(
        "salt.modules.freezer.status",
        MagicMock(return_value=True),
    ), patch("salt.utils.json.load", load), patch(
        "salt.modules.freezer.fopen",
        fopen,
    ):
        assert freezer.restore() == {
            "pkgs": {"add": [], "remove": []},
            "repos": {"add": ["missing-repo"], "remove": []},
            "comment": [],
        }
        salt_mock["pkg.list_pkgs"].assert_called()
        salt_mock["pkg.list_repos"].assert_called()
        salt_mock["pkg.mod_repo"].assert_called_once()
        fopen.assert_called()
        load.assert_called()


def test_restore_add_missing_package():
    """
    Test to restore an old state
    """
    # Only a missing package is installed
    fopen = MagicMock()
    load = MagicMock(side_effect=[{"missing-package": {}}, {}])
    salt_mock = {
        "pkg.list_pkgs": MagicMock(return_value={}),
        "pkg.list_repos": MagicMock(return_value={}),
        "pkg.install": MagicMock(),
    }
    with patch.dict(freezer.__salt__, salt_mock), patch(
        "salt.modules.freezer.status",
        MagicMock(return_value=True),
    ), patch("salt.utils.json.load", load), patch(
        "salt.modules.freezer.fopen",
        fopen,
    ):
        assert freezer.restore() == {
            "pkgs": {"add": ["missing-package"], "remove": []},
            "repos": {"add": [], "remove": []},
            "comment": [],
        }
        salt_mock["pkg.list_pkgs"].assert_called()
        salt_mock["pkg.list_repos"].assert_called()
        salt_mock["pkg.install"].assert_called_once()
        fopen.assert_called()
        load.assert_called()


def test_restore_remove_extra_package():
    """
    Test to restore an old state
    """
    # Only an extra package is removed
    salt_mock = {
        "pkg.list_pkgs": MagicMock(return_value={"extra-package": {}}),
        "pkg.list_repos": MagicMock(return_value={}),
        "pkg.remove": MagicMock(),
    }
    fopen = MagicMock()
    load = MagicMock(side_effect=[{}, {}])
    with patch.dict(freezer.__salt__, salt_mock), patch(
        "salt.modules.freezer.status",
        MagicMock(return_value=True),
    ), patch("salt.utils.json.load", load), patch(
        "salt.modules.freezer.fopen",
        fopen,
    ):
        assert freezer.restore() == {
            "pkgs": {"add": [], "remove": ["extra-package"]},
            "repos": {"add": [], "remove": []},
            "comment": [],
        }
        salt_mock["pkg.list_pkgs"].assert_called()
        salt_mock["pkg.list_repos"].assert_called()
        salt_mock["pkg.remove"].assert_called_once()
        fopen.assert_called()
        load.assert_called()


def test_restore_remove_extra_repo():
    """
    Test to restore an old state
    """
    # Only an extra repository is removed
    salt_mock = {
        "pkg.list_pkgs": MagicMock(return_value={}),
        "pkg.list_repos": MagicMock(return_value={"extra-repo": {}}),
        "pkg.del_repo": MagicMock(),
    }
    fopen = MagicMock()
    load = MagicMock(side_effect=[{}, {}])
    with patch.dict(freezer.__salt__, salt_mock), patch(
        "salt.modules.freezer.status",
        MagicMock(return_value=True),
    ), patch("salt.utils.json.load", load), patch(
        "salt.modules.freezer.fopen",
        fopen,
    ):
        assert freezer.restore() == {
            "pkgs": {"add": [], "remove": []},
            "repos": {"add": [], "remove": ["extra-repo"]},
            "comment": [],
        }
        salt_mock["pkg.list_pkgs"].assert_called()
        salt_mock["pkg.list_repos"].assert_called()
        salt_mock["pkg.del_repo"].assert_called_once()
        fopen.assert_called()
        load.assert_called()


def test_restore_clean_yml():
    """
    Test to restore an old state
    """
    salt_mock = {
        "pkg.list_pkgs": MagicMock(return_value={}),
        "pkg.list_repos": MagicMock(return_value={}),
        "pkg.install": MagicMock(),
    }
    fopen = MagicMock()
    load = MagicMock()
    remove = MagicMock()
    with patch.dict(freezer.__salt__, salt_mock), patch(
        "salt.modules.freezer.status",
        MagicMock(return_value=True),
    ), patch("salt.utils.json.load", load), patch("salt.modules.freezer.fopen", fopen,), patch(
        "os.remove", remove
    ):
        assert freezer.restore(clean=True) == {
            "pkgs": {"add": [], "remove": []},
            "repos": {"add": [], "remove": []},
            "comment": [],
        }
        salt_mock["pkg.list_pkgs"].assert_called()
        salt_mock["pkg.list_repos"].assert_called()
        fopen.assert_called()
        load.assert_called()
        assert remove.call_count == 2


def test_compare_no_args():
    """
    Test freezer.compare with no arguments
    """
    with pytest.raises(TypeError):
        freezer.compare()  # pylint: disable=no-value-for-parameter


def test_compare_not_enough_args():
    """
    Test freezer.compare without enough arguments
    """
    with pytest.raises(TypeError):
        freezer.compare(None)  # pylint: disable=no-value-for-parameter


def test_compare_too_many_args():
    """
    Test freezer.compare with too many arguments
    """
    with pytest.raises(TypeError):
        freezer.compare(None, None, None)  # pylint: disable=too-many-function-args


def test_compare_no_names():
    """
    Test freezer.compare with no real freeze names as arguments
    """
    with pytest.raises(CommandExecutionError):
        freezer.compare(old=None, new=None)
