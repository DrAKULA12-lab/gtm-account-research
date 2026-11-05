import pytest

from acr.cli import main, parse_file


def test_check_playbooks_exits_cleanly():
    with pytest.raises(SystemExit) as exc:
        main(["--check-playbooks"])
    assert exc.value.code == 0


def test_no_arguments_is_an_error():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_parse_file(tmp_path):
    f = tmp_path / "domains.txt"
    f.write_text("# comment\n\nhubspot.com,hubspot\nnotion.so\n")
    assert parse_file(f) == [("hubspot.com", "hubspot"), ("notion.so", None)]
