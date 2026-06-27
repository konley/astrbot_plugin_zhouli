"""Behavior tests for astrbot_plugin_zhouli."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── _parse_args ────────────────────────────────────


@pytest.fixture
def plugin():
    """Create a plugin instance with mocked Context."""
    from main import ZhouLi

    mock_ctx = MagicMock()
    mock_ctx.get_using_provider.return_value = None
    return ZhouLi(mock_ctx)


class TestParseArgs:
    def test_only_text(self, plugin):
        length, tone, content = plugin._parse_args("周礼 今天天气真好")
        assert length == "成礼"
        assert tone == "自动"
        assert content == "今天天气真好"

    def test_length_and_text(self, plugin):
        length, tone, content = plugin._parse_args("周礼 小礼 今天天气真好")
        assert length == "小礼"
        assert content == "今天天气真好"

    def test_tone_and_text(self, plugin):
        length, tone, content = plugin._parse_args("周礼 辩经 今天天气真好")
        assert tone == "大儒辩经"
        assert content == "今天天气真好"

    def test_length_tone_and_text(self, plugin):
        length, tone, content = plugin._parse_args("周礼 大礼 痛心 今天天气真好")
        assert length == "大礼"
        assert tone == "痛心疾首"
        assert content == "今天天气真好"

    def test_no_content(self, plugin):
        length, tone, content = plugin._parse_args("周礼")
        assert content == ""


class TestIsHelp:
    def test_help_keyword(self, plugin):
        assert plugin._is_help("help")
        assert plugin._is_help("帮助")
        assert plugin._is_help("?")

    def test_help_with_prefix(self, plugin):
        assert plugin._is_help("周礼 help")
        assert plugin._is_help("周礼 帮助")

    def test_not_help(self, plugin):
        assert not plugin._is_help("周礼 今天天气真好")


class TestStripMarkdown:
    def test_remove_bold(self):
        from main import ZhouLi

        assert ZhouLi._strip_markdown("**hello** world") == "hello world"

    def test_remove_heading(self):
        from main import ZhouLi

        assert ZhouLi._strip_markdown("# title\ncontent") == "title\ncontent"
