import pytest
import salt.modules.test as testmod
import saltext.freezer.modules.freezer_mod as freezer_module
import saltext.freezer.states.freezer_mod as freezer_state


@pytest.fixture
def configure_loader_modules():
    return {
        freezer_module: {
            "__salt__": {
                "test.echo": testmod.echo,
            },
        },
        freezer_state: {
            "__salt__": {
                "freezer.example_function": freezer_module.example_function,
            },
        },
    }


def test_replace_this_this_with_something_meaningful():
    echo_str = "Echoed!"
    expected = {
        "name": echo_str,
        "changes": {},
        "result": True,
        "comment": f"The 'freezer.example_function' returned: '{echo_str}'",
    }
    assert freezer_state.exampled(echo_str) == expected
