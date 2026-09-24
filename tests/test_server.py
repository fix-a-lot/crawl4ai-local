import os

import pytest

from crawl4ai_local.server import (
    _is_blocked_system_path,
    _parse_field_spec,
    _to_mount_path,
)


class TestToMountPath:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            (r"C:\Users\me\shot.png", "/mnt/c/Users/me/shot.png"),
            ("D:/data/shot.png", "/mnt/d/data/shot.png"),
            ("/home/me/shot.png", "/home/me/shot.png"),
            ("shot.png", "shot.png"),
        ],
    )
    def test_converts_only_windows_drive_paths(self, path, expected):
        assert _to_mount_path(path) == expected


class TestIsBlockedSystemPath:
    def test_empty_path_is_blocked(self):
        assert _is_blocked_system_path("") is True

    @pytest.mark.parametrize(
        "path",
        [
            "/etc/evil.png",
            "/etc",
            "/usr/bin/evil.png",
            "/usr/../etc/evil.png",
            "//etc/evil.png",
            "/boot/evil.png",
            "/proc/self/evil.png",
            "/var/lib/evil.png",
        ],
    )
    def test_blocks_linux_system_paths(self, path):
        assert _is_blocked_system_path(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "/mnt/c/Windows/evil.png",
            "/mnt/c/windows/evil.png",
            "/mnt/d/Program Files/evil.png",
            "/mnt/c/Program Files (x86)/evil.png",
            "/mnt/c/ProgramData/evil.png",
            "/mnt/c/Users/All Users/evil.png",
            "/mnt/c/Users/Default/evil.png",
            r"C:\Windows\evil.png",
            r"c:\program files\evil.png",
        ],
    )
    def test_blocks_windows_system_paths(self, path):
        assert _is_blocked_system_path(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "/etc2/evil.png",
            "/mnt/c/Windows2/evil.png",
            "/mnt/c/Users/Defaults/evil.png",
        ],
    )
    def test_does_not_block_sibling_named_path(self, path):
        assert _is_blocked_system_path(path) is False

    @pytest.mark.parametrize(
        "path",
        [
            "/home/me/shot.png",
            "/tmp/shot.png",
            "/mnt/c/Users/me/Desktop/shot.png",
            r"C:\Users\me\Desktop\shot.png",
        ],
    )
    def test_does_not_block_ordinary_path(self, path):
        assert _is_blocked_system_path(path) is False

    def test_blocks_relative_traversal_into_system_path(self, tmp_path, monkeypatch):
        # CWD 기준 상대경로가 실제로는 시스템 경로를 가리키는 경우.
        # abspath로 먼저 절대경로화하지 않으면 이 케이스를 놓친다.
        monkeypatch.chdir(tmp_path)
        depth = len(tmp_path.parts) - 1  # 루트("/") 제외
        traversal = "../" * depth + "etc/evil.png"
        assert _is_blocked_system_path(traversal) is True

    def test_blocks_symlink_into_system_path(self, tmp_path):
        link = tmp_path / "link"
        os.symlink("/etc", link)
        assert _is_blocked_system_path(str(link / "evil.png")) is True


class TestParseFieldSpec:
    def test_attribute_with_selector(self):
        assert _parse_field_spec("a@href") == {
            "name": "",
            "type": "attribute",
            "attribute": "href",
            "selector": "a",
        }

    def test_attribute_on_base_element(self):
        assert _parse_field_spec("@data-value") == {
            "name": "",
            "type": "attribute",
            "attribute": "data-value",
        }

    def test_text_with_explicit_suffix(self):
        assert _parse_field_spec("td:text") == {
            "name": "",
            "type": "text",
            "selector": "td",
        }

    def test_text_without_suffix(self):
        assert _parse_field_spec("td") == {
            "name": "",
            "type": "text",
            "selector": "td",
        }

    def test_text_suffix_only_stripped_at_end(self):
        # selector 자체에 "text"가 부분 문자열로 들어있어도 깨지면 안 된다.
        assert _parse_field_spec(".text-bold:text") == {
            "name": "",
            "type": "text",
            "selector": ".text-bold",
        }
