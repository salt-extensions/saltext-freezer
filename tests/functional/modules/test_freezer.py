import pytest

pytestmark = [
    pytest.mark.requires_salt_modules("freezer.example_function"),
]


@pytest.fixture
def freezer(modules):
    return modules.freezer


def test_replace_this_this_with_something_meaningful(freezer):
    echo_str = "Echoed!"
    res = freezer.example_function(echo_str)
    assert res == echo_str
