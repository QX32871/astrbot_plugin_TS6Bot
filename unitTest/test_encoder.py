"""
命令编码器单元测试
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ts6query.protocol.encoder import CommandEncoder


class TestCommandEncoder:
    """命令编码器测试"""

    def test_escape_backslash(self):
        """测试反斜杠转义"""
        result = CommandEncoder.escape("test\\value")
        assert result == "test\\\\value"

    def test_escape_slash(self):
        """测试斜杠转义"""
        result = CommandEncoder.escape("test/value")
        assert result == "test\\/value"

    def test_escape_space(self):
        """测试空格转义"""
        result = CommandEncoder.escape("test value")
        assert result == "test\\svalue"

    def test_escape_pipe(self):
        """测试管道符转义"""
        result = CommandEncoder.escape("test|value")
        assert result == "test\\pvalue"

    def test_escape_newline(self):
        """测试换行符转义"""
        result = CommandEncoder.escape("test\nvalue")
        assert result == "test\\nvalue"

    def test_escape_carriage_return(self):
        """测试回车符转义"""
        result = CommandEncoder.escape("test\rvalue")
        assert result == "test\\rvalue"

    def test_escape_tab(self):
        """测试制表符转义"""
        result = CommandEncoder.escape("test\tvalue")
        assert result == "test\\tvalue"

    def test_escape_multiple_chars(self):
        """测试多字符转义"""
        result = CommandEncoder.escape("hello world/test\\data")
        assert result == "hello\\sworld\\/test\\\\data"

    def test_encode_value_string(self):
        """测试字符串值编码"""
        result = CommandEncoder.encode_value("hello world")
        assert result == "hello\\sworld"

    def test_encode_value_int(self):
        """测试整数值编码"""
        result = CommandEncoder.encode_value(123)
        assert result == "123"

    def test_encode_value_float(self):
        """测试浮点数值编码"""
        result = CommandEncoder.encode_value(3.14)
        assert result == "3.14"

    def test_encode_value_bool_true(self):
        """测试布尔值 True 编码"""
        result = CommandEncoder.encode_value(True)
        assert result == "1"

    def test_encode_value_bool_false(self):
        """测试布尔值 False 编码"""
        result = CommandEncoder.encode_value(False)
        assert result == "0"

    def test_encode_value_none(self):
        """测试 None 值编码"""
        result = CommandEncoder.encode_value(None)
        assert result == ""

    def test_encode_value_list(self):
        """测试列表值编码"""
        result = CommandEncoder.encode_value(["a", "b", "c"])
        assert result == "a|b|c"

    def test_encode_value_list_with_spaces(self):
        """测试包含空格的列表值编码"""
        result = CommandEncoder.encode_value(["hello world", "foo bar"])
        assert result == "hello\\sworld|foo\\sbar"

    def test_encode_command_no_params(self):
        """测试无参数命令编码"""
        result = CommandEncoder.encode_command("serverlist")
        assert result == "serverlist"

    def test_encode_command_with_params(self):
        """测试带参数命令编码"""
        result = CommandEncoder.encode_command("clientmove", {"clid": 1, "cid": 2})
        assert result == "clientmove clid=1 cid=2"

    def test_encode_command_with_escaped_param(self):
        """测试带转义参数的命令编码"""
        result = CommandEncoder.encode_command(
            "clientkick", {"clid": 1, "reasonmsg": "bye bye"}
        )
        assert result == "clientkick clid=1 reasonmsg=bye\\sbye"

    def test_encode_command_with_none_param(self):
        """测试带 None 参数的命令编码（标志参数）"""
        result = CommandEncoder.encode_command("whoami", {"none_param": None})
        # None 值会被转换为标志参数形式
        assert "-none_param" in result

    def test_encode_command_with_options(self):
        """测试带选项的命令编码"""
        result = CommandEncoder.encode_command_with_options(
            "clientlist", {}, ["uid", "country"]
        )
        assert result == "clientlist -uid -country"

    def test_encode_command_with_params_and_options(self):
        """测试带参数和选项的命令编码"""
        result = CommandEncoder.encode_command_with_options(
            "clientlist", {"count": 10}, ["uid"]
        )
        assert "clientlist" in result
        assert "count=10" in result
        assert "-uid" in result

    def test_encode_chinese_characters(self):
        """测试中文字符编码（不应转义）"""
        result = CommandEncoder.encode_value("你好世界")
        assert result == "你好世界"

    def test_encode_complex_scenario(self):
        """测试复杂场景编码"""
        # 模拟踢出用户命令，带中文原因
        result = CommandEncoder.encode_command(
            "clientkick",
            {"clid": 5, "reasonid": 5, "reasonmsg": "违规操作 禁言处理"}
        )
        assert "clientkick" in result
        assert "clid=5" in result
        assert "reasonid=5" in result
        # 空格应该被转义
        assert "reasonmsg=违规操作\\s禁言处理" in result
