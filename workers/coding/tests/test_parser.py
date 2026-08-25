import pytest

from workers.coding.parser import ActionParseError, parse_action


def test_parse_plain_json_action():
    assert parse_action('{"action":"list_files"}') == {"action": "list_files"}


def test_parse_json_fence():
    assert parse_action('```json\n{"action":"git_status"}\n```') == {
        "action": "git_status"
    }


def test_rejects_unknown_action():
    with pytest.raises(ActionParseError):
        parse_action('{"action":"delete_everything"}')
