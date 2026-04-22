"""
响应解析器单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ts6query.protocol.parser import ResponseParser
from ts6query.protocol.types import QueryResponse


class TestResponseParser:
    """响应解析器测试"""

    def test_unescape_backslash(self):
        """测试反斜杠反转义"""
        result = ResponseParser.unescape("test\\\\value")
        assert result == "test\\value"

    def test_unescape_slash(self):
        """测试斜杠反转义"""
        result = ResponseParser.unescape("test\\/value")
        assert result == "test/value"

    def test_unescape_space(self):
        """测试空格反转义"""
        result = ResponseParser.unescape("test\\svalue")
        assert result == "test value"

    def test_unescape_pipe(self):
        """测试管道符反转义"""
        result = ResponseParser.unescape("test\\pvalue")
        assert result == "test|value"

    def test_unescape_newline(self):
        """测试换行符反转义"""
        result = ResponseParser.unescape("test\\nvalue")
        assert result == "test\nvalue"

    def test_unescape_multiple(self):
        """测试多字符反转义"""
        result = ResponseParser.unescape("hello\\sworld\\/test\\\\data")
        assert result == "hello world/test\\data"

    def test_parse_value_empty(self):
        """测试空值解析"""
        result = ResponseParser.parse_value("")
        assert result == ""

    def test_parse_value_int(self):
        """测试整数值解析"""
        result = ResponseParser.parse_value("123")
        assert result == 123
        assert isinstance(result, int)

    def test_parse_value_float(self):
        """测试浮点数值解析"""
        result = ResponseParser.parse_value("3.14")
        assert result == 3.14
        assert isinstance(result, float)

    def test_parse_value_bool_false(self):
        """测试布尔值 False 解析"""
        result = ResponseParser.parse_value("0")
        assert result is False

    def test_parse_value_bool_true(self):
        """测试布尔值 True 解析"""
        result = ResponseParser.parse_value("1")
        assert result is True

    def test_parse_value_string(self):
        """测试字符串值解析"""
        result = ResponseParser.parse_value("hello")
        assert result == "hello"

    def test_parse_value_escaped_string(self):
        """测试转义字符串值解析"""
        result = ResponseParser.parse_value("hello\\sworld")
        assert result == "hello world"

    def test_parse_key_value_pairs_empty(self):
        """测试空键值对解析"""
        result = ResponseParser.parse_key_value_pairs("")
        assert result == {}

    def test_parse_key_value_pairs_single(self):
        """测试单个键值对解析"""
        result = ResponseParser.parse_key_value_pairs("name=test")
        assert result == {"name": "test"}

    def test_parse_key_value_pairs_multiple(self):
        """测试多个键值对解析"""
        result = ResponseParser.parse_key_value_pairs("name=test value=123")
        assert result == {"name": "test", "value": 123}

    def test_parse_key_value_pairs_with_spaces(self):
        """测试包含空格的键值对解析"""
        result = ResponseParser.parse_key_value_pairs("name=hello\\sworld")
        assert result == {"name": "hello world"}

    def test_parse_response_error_only(self):
        """测试仅错误行的响应解析"""
        result = ResponseParser.parse_response("error id=0 msg=ok")
        assert result.success is True
        assert result.error_id == 0
        assert result.error_msg == "ok"
        assert result.data == []

    def test_parse_response_error_with_msg(self):
        """测试带错误消息的响应解析"""
        result = ResponseParser.parse_response("error id=256 msg=invalid\\sclientid")
        assert result.success is False
        assert result.error_id == 256
        assert result.error_msg == "invalid clientid"

    def test_parse_response_with_data(self):
        """测试带数据行的响应解析"""
        raw = "virtualserver_name=Test\\sServer virtualserver_port=9987\nerror id=0 msg=ok"
        result = ResponseParser.parse_response(raw)
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["virtualserver_name"] == "Test Server"
        assert result.data[0]["virtualserver_port"] == 9987

    def test_parse_response_multiple_data_items(self):
        """测试多数据项响应解析（使用 | 分隔）"""
        raw = "clid=1 cid=2|clid=3 cid=4\nerror id=0 msg=ok"
        result = ResponseParser.parse_response(raw)
        assert result.success is True
        assert len(result.data) == 2
        assert result.data[0]["clid"] == 1
        assert result.data[0]["cid"] == 2
        assert result.data[1]["clid"] == 3
        assert result.data[1]["cid"] == 4

    def test_parse_response_empty(self):
        """测试空响应解析"""
        result = ResponseParser.parse_response("")
        assert result.success is False
        assert result.error_id == -1

    def test_parse_event_valid(self):
        """测试有效事件解析"""
        result = ResponseParser.parse_event("notifycliententerview clid=5 cid=2")
        assert result is not None
        assert result["event_name"] == "notifycliententerview"
        assert result["data"]["clid"] == 5
        assert result["data"]["cid"] == 2

    def test_parse_event_invalid(self):
        """测试无效事件解析"""
        result = ResponseParser.parse_event("error id=0 msg=ok")
        assert result is None

    def test_parse_event_empty(self):
        """测试空事件解析"""
        result = ResponseParser.parse_event("")
        assert result is None


class TestQueryResponse:
    """QueryResponse 测试"""

    def test_first_property_with_data(self):
        """测试 first 属性（有数据）"""
        response = QueryResponse(
            success=True,
            error_id=0,
            error_msg="ok",
            data=[{"name": "test", "value": 1}]
        )
        assert response.first == {"name": "test", "value": 1}

    def test_first_property_no_data(self):
        """测试 first 属性（无数据）"""
        response = QueryResponse(
            success=True,
            error_id=0,
            error_msg="ok",
            data=[]
        )
        assert response.first is None

    def test_has_data_true(self):
        """测试 has_data 属性（有数据）"""
        response = QueryResponse(
            success=True,
            error_id=0,
            error_msg="ok",
            data=[{"name": "test"}]
        )
        assert response.has_data is True

    def test_has_data_false(self):
        """测试 has_data 属性（无数据）"""
        response = QueryResponse(
            success=True,
            error_id=0,
            error_msg="ok",
            data=[]
        )
        assert response.has_data is False

    def test_real_world_serverlist_response(self):
        """测试真实服务器列表响应"""
        raw = (
            "virtualserver_id=1 virtualserver_port=9987 virtualserver_status=online "
            "virtualserver_clientsonline=5 virtualserver_queryclientsonline=1 "
            "virtualserver_maxclients=32 virtualserver_uptime=12345 "
            "virtualserver_name=My\\sServer\n"
            "error id=0 msg=ok"
        )
        result = ResponseParser.parse_response(raw)
        assert result.success is True
        assert len(result.data) == 1
        server = result.data[0]
        assert server["virtualserver_id"] == 1
        assert server["virtualserver_port"] == 9987
        assert server["virtualserver_status"] == "online"
        assert server["virtualserver_clientsonline"] == 5
        assert server["virtualserver_name"] == "My Server"

    def test_real_world_clientlist_response(self):
        """测试真实用户列表响应"""
        raw = (
            "clid=1 cid=2 client_nickname=Admin client_type=0|"
            "clid=2 cid=3 client_nickname=User\\s1 client_type=0|"
            "clid=3 cid=4 client_nickname=User\\s2 client_type=0\n"
            "error id=0 msg=ok"
        )
        result = ResponseParser.parse_response(raw)
        assert result.success is True
        assert len(result.data) == 3
        assert result.data[0]["client_nickname"] == "Admin"
        assert result.data[1]["client_nickname"] == "User 1"
        assert result.data[2]["client_nickname"] == "User 2"
