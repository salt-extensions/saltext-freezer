import pytest

pytestmark = [
    pytest.mark.requires_salt_states("freezer.exampled"),
]


@pytest.fixture
def freezer(states):
    return states.freezer


def test_replace_this_this_with_something_meaningful(freezer):
    echo_str = "Echoed!"
    ret = freezer.exampled(echo_str)
    assert ret.result
    assert not ret.changes
    assert echo_str in ret.comment
