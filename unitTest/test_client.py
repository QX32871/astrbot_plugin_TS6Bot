"""
客户端单元测试

使用 mock 模拟连接和响应。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ts6query import TS6QueryClient
from ts6query.protocol.types import ConnectionType, QueryResponse
from ts6query.exceptions import NotConnectedError, CommandError, AuthenticationError


class TestTS6QueryClient:
    """TS6QueryClient 测试"""

    @pytest.fixture
    def client(self):
        """创建客户端实例"""
        return TS6QueryClient()

    def test_init(self, client):
        """测试初始化"""
        assert client.is_connected is False
        assert client.is_authenticated is False
        assert client.current_server_id is None

    def test_repr(self, client):
        """测试字符串表示"""
        result = repr(client)
        assert "未连接" in result
        assert "未认证" in result

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, client):
        """测试未连接时断开连接"""
        # 应该不会抛出异常
        await client.disconnect()
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_execute_without_connection(self, client):
        """测试未连接时执行命令"""
        with pytest.raises(NotConnectedError):
            await client.execute("serverlist")

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """测试异步上下文管理器"""
        async with TS6QueryClient() as c:
            assert isinstance(c, TS6QueryClient)


class TestTS6QueryClientWithMock:
    """使用 Mock 的客户端测试"""

    @pytest.fixture
    def mock_connection(self):
        """创建模拟连接"""
        mock = MagicMock()
        mock.is_connected = True
        mock.send_and_receive = AsyncMock()
        mock.connect = AsyncMock()
        mock.disconnect = AsyncMock()
        return mock

    @pytest.fixture
    def client_with_mock(self, mock_connection):
        """创建带模拟连接的客户端"""
        client = TS6QueryClient()
        client._connection = mock_connection
        client._connected = True
        return client

    @pytest.mark.asyncio
    async def test_server_list_success(self, client_with_mock, mock_connection):
        """测试获取服务器列表成功"""
        mock_response = (
            "virtualserver_id=1 virtualserver_port=9987 virtualserver_status=online "
            "virtualserver_clientsonline=5 virtualserver_queryclientsonline=1 "
            "virtualserver_maxclients=32 virtualserver_uptime=12345 virtualserver_name=Test\\sServer\n"
            "error id=0 msg=ok"
        )
        mock_connection.send_and_receive.return_value = mock_response

        result = await client_with_mock.server_list()

        assert len(result) == 1
        assert result[0]["virtualserver_id"] == 1
        assert result[0]["virtualserver_name"] == "Test Server"

    @pytest.mark.asyncio
    async def test_server_info_success(self, client_with_mock, mock_connection):
        """测试获取服务器信息成功"""
        mock_response = (
            "virtualserver_unique_identifier=abc123 virtualserver_name=Test\\sServer "
            "virtualserver_welcomemessage=Welcome virtualserver_platform=Windows "
            "virtualserver_version=3.13.0 virtualserver_maxclients=32 "
            "virtualserver_clientsonline=10 virtualserver_queryclientsonline=2 "
            "virtualserver_channelsonline=15 virtualserver_created=1609459200 "
            "virtualserver_uptime=86400 virtualserver_port=9987 "
            "virtualserver_autostart=1 virtualserver_hostmessage=Hello "
            "virtualserver_hostmessage_mode=1 virtualserver_default_server_group=1 "
            "virtualserver_default_channel_group=1 virtualserver_password=0 "
            "virtualserver_reserved_slots=5 virtualserver_icon_id=0 "
            "virtualserver_total_packetloss_speech=0 virtualserver_total_packetloss_keepalive=0 "
            "virtualserver_total_ping=15.5\n"
            "error id=0 msg=ok"
        )
        mock_connection.send_and_receive.return_value = mock_response

        result = await client_with_mock.server_info()

        assert result["virtualserver_name"] == "Test Server"
        assert result["virtualserver_clientsonline"] == 10

    @pytest.mark.asyncio
    async def test_client_list_success(self, client_with_mock, mock_connection):
        """测试获取用户列表成功"""
        mock_response = (
            "clid=1 cid=2 client_database_id=100 client_nickname=Admin client_type=0|"
            "clid=2 cid=3 client_database_id=101 client_nickname=User\\s1 client_type=0\n"
            "error id=0 msg=ok"
        )
        mock_connection.send_and_receive.return_value = mock_response

        result = await client_with_mock.client_list()

        assert len(result) == 2
        assert result[0]["client_nickname"] == "Admin"
        assert result[1]["client_nickname"] == "User 1"

    @pytest.mark.asyncio
    async def test_client_kick_success(self, client_with_mock, mock_connection):
        """测试踢出用户成功"""
        mock_response = "error id=0 msg=ok"
        mock_connection.send_and_receive.return_value = mock_response

        # 不应该抛出异常
        await client_with_mock.client_kick(1, 5, "测试踢出")

        # 验证命令被发送
        mock_connection.send_and_receive.assert_called_once()
        call_args = mock_connection.send_and_receive.call_args[0][0]
        assert "clientkick" in call_args
        assert "clid=1" in call_args

    @pytest.mark.asyncio
    async def test_client_move_success(self, client_with_mock, mock_connection):
        """测试移动用户成功"""
        mock_response = "error id=0 msg=ok"
        mock_connection.send_and_receive.return_value = mock_response

        await client_with_mock.client_move(1, 10)

        call_args = mock_connection.send_and_receive.call_args[0][0]
        assert "clientmove" in call_args
        assert "clid=1" in call_args
        assert "cid=10" in call_args

    @pytest.mark.asyncio
    async def test_ban_add_success(self, client_with_mock, mock_connection):
        """测试添加封禁成功"""
        mock_response = "banid=123\nerror id=0 msg=ok"
        mock_connection.send_and_receive.return_value = mock_response

        result = await client_with_mock.ban_add(name="BadUser", reason="违规")

        assert result == 123

    @pytest.mark.asyncio
    async def test_command_error(self, client_with_mock, mock_connection):
        """测试命令执行失败"""
        mock_response = "error id=256 msg=invalid\\sclientid"
        mock_connection.send_and_receive.return_value = mock_response

        with pytest.raises(CommandError) as exc_info:
            await client_with_mock.client_info(999)

        assert exc_info.value.error_id == 256

    @pytest.mark.asyncio
    async def test_version_success(self, client_with_mock, mock_connection):
        """测试获取版本信息成功"""
        mock_response = "version=3.13.0 build=12345 platform=Windows\nerror id=0 msg=ok"
        mock_connection.send_and_receive.return_value = mock_response

        result = await client_with_mock.version()

        assert result["version"] == "3.13.0"
        assert result["build"] == 12345
        assert result["platform"] == "Windows"


class TestConnectionType:
    """连接类型测试"""

    def test_tcp_value(self):
        """测试 TCP 连接类型值"""
        assert ConnectionType.TCP.value == "tcp"

    def test_ssh_value(self):
        """测试 SSH 连接类型值"""
        assert ConnectionType.SSH.value == "ssh"

    def test_enum_comparison(self):
        """测试枚举比较"""
        assert ConnectionType.TCP == ConnectionType.TCP
        assert ConnectionType.TCP != ConnectionType.SSH
