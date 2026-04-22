"""
异常类单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ts6query.exceptions import (
    TS6QueryError,
    ConnectionError,
    AuthenticationError,
    CommandError,
    ParseError,
    TimeoutError,
    NotConnectedError,
)


class TestTS6QueryError:
    """TS6QueryError 基础异常测试"""

    def test_message_only(self):
        """测试仅消息的异常"""
        exc = TS6QueryError("测试错误")
        assert exc.message == "测试错误"
        assert exc.details == {}
        assert str(exc) == "测试错误"

    def test_message_with_details(self):
        """测试带详情的异常"""
        exc = TS6QueryError("测试错误", {"key": "value"})
        assert exc.message == "测试错误"
        assert exc.details == {"key": "value"}
        assert "测试错误" in str(exc)
        assert "key" in str(exc)


class TestConnectionError:
    """ConnectionError 测试"""

    def test_basic_error(self):
        """测试基本连接错误"""
        exc = ConnectionError("连接失败")
        assert exc.message == "连接失败"
        assert exc.host is None
        assert exc.port is None

    def test_with_host_port(self):
        """测试带主机端口的错误"""
        exc = ConnectionError("连接失败", host="localhost", port=10011)
        assert exc.host == "localhost"
        assert exc.port == 10011
        assert "localhost:10011" in str(exc)

    def test_with_all_params(self):
        """测试完整参数"""
        exc = ConnectionError(
            "连接失败",
            host="192.168.1.1",
            port=10022,
            details={"timeout": 10}
        )
        assert exc.host == "192.168.1.1"
        assert exc.port == 10022
        assert exc.details == {"timeout": 10}
        assert "192.168.1.1:10022" in str(exc)


class TestAuthenticationError:
    """AuthenticationError 测试"""

    def test_default_message(self):
        """测试默认消息"""
        exc = AuthenticationError()
        assert exc.message == "认证失败"

    def test_with_username(self):
        """测试带用户名的错误"""
        exc = AuthenticationError(username="serveradmin")
        assert exc.username == "serveradmin"

    def test_with_error_id(self):
        """测试带错误 ID"""
        exc = AuthenticationError(error_id=520)
        assert exc.error_id == 520


class TestCommandError:
    """CommandError 测试"""

    def test_basic_error(self):
        """测试基本命令错误"""
        exc = CommandError("命令失败")
        assert exc.message == "命令失败"
        assert exc.command is None

    def test_with_command(self):
        """测试带命令名的错误"""
        exc = CommandError("命令失败", command="clientkick")
        assert exc.command == "clientkick"
        assert "[clientkick]" in str(exc)

    def test_with_error_info(self):
        """测试带错误信息的错误"""
        exc = CommandError(
            "命令失败",
            command="clientkick",
            error_id=256,
            error_msg="invalid client id"
        )
        assert exc.error_id == 256
        assert exc.error_msg == "invalid client id"
        assert "错误ID: 256" in str(exc)
        assert "invalid client id" in str(exc)

    def test_full_str_representation(self):
        """测试完整字符串表示"""
        exc = CommandError(
            "执行失败",
            command="banadd",
            error_id=1538,
            error_msg="invalid ban time"
        )
        result = str(exc)
        assert "[banadd]" in result
        assert "执行失败" in result
        assert "错误ID: 1538" in result
        assert "invalid ban time" in result


class TestParseError:
    """ParseError 测试"""

    def test_basic_error(self):
        """测试基本解析错误"""
        exc = ParseError("解析失败")
        assert exc.message == "解析失败"
        assert exc.raw_data is None

    def test_with_raw_data(self):
        """测试带原始数据的错误"""
        exc = ParseError("解析失败", raw_data="invalid response")
        assert exc.raw_data == "invalid response"
        assert "invalid response" in str(exc)

    def test_with_long_raw_data(self):
        """测试长原始数据截断"""
        long_data = "x" * 200
        exc = ParseError("解析失败", raw_data=long_data)
        assert "..." in str(exc)
        assert len(exc.raw_data) == 200


class TestTimeoutError:
    """TimeoutError 测试"""

    def test_default_message(self):
        """测试默认消息"""
        exc = TimeoutError()
        assert exc.message == "操作超时"

    def test_with_timeout_seconds(self):
        """测试带超时秒数"""
        exc = TimeoutError(timeout_seconds=10.0)
        assert exc.timeout_seconds == 10.0
        assert "10.0秒" in str(exc)

    def test_custom_message(self):
        """测试自定义消息"""
        exc = TimeoutError("连接超时", timeout_seconds=30)
        assert exc.message == "连接超时"
        assert "30秒" in str(exc)


class TestNotConnectedError:
    """NotConnectedError 测试"""

    def test_default_message(self):
        """测试默认消息"""
        exc = NotConnectedError()
        assert exc.message == "未连接到服务器"

    def test_custom_message(self):
        """测试自定义消息"""
        exc = NotConnectedError("请先调用 connect()")
        assert exc.message == "请先调用 connect()"


class TestExceptionInheritance:
    """异常继承关系测试"""

    def test_all_inherit_from_base(self):
        """测试所有异常都继承自 TS6QueryError"""
        assert issubclass(ConnectionError, TS6QueryError)
        assert issubclass(AuthenticationError, TS6QueryError)
        assert issubclass(CommandError, TS6QueryError)
        assert issubclass(ParseError, TS6QueryError)
        assert issubclass(TimeoutError, TS6QueryError)
        assert issubclass(NotConnectedError, TS6QueryError)

    def test_can_catch_with_base(self):
        """测试可以用基类捕获所有异常"""
        exceptions = [
            ConnectionError("连接失败"),
            AuthenticationError("认证失败"),
            CommandError("命令失败"),
            ParseError("解析失败"),
            TimeoutError("超时"),
            NotConnectedError(),
        ]

        for exc in exceptions:
            assert isinstance(exc, TS6QueryError)
