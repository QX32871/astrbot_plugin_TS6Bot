"""
TS6QueryClient 主类

TeamSpeak 6 ServerQuery 客户端。
"""

from typing import Optional, Dict, Any, List
from .connection import TCPConnection, SSHConnection, ConnectionBase, TCPConnectionPool, ConnectionTimeout
from .protocol import ConnectionType, QueryResponse, CommandEncoder, ResponseParser
from .exceptions import (
    TS6QueryError,
    ConnectionError,
    AuthenticationError,
    CommandError,
    NotConnectedError,
)


class TS6QueryClient:
    """
    TeamSpeak 6 ServerQuery 客户端

    支持通过 TCP 或 SSH 连接到 TeamSpeak 服务器，
    执行 ServerQuery 命令并获取响应。

    使用示例:
        async with TS6QueryClient() as client:
            await client.connect(
                host="localhost",
                username="serveradmin",
                password="password"
            )
            info = await client.server_info()
            print(info)
    """

    def __init__(self, timeout: float = 10.0, use_pool: bool = False, max_pool_size: int = 10):
        """
        初始化客户端

        Args:
            timeout: 默认超时时间（秒）
            use_pool: 是否使用连接池
            max_pool_size: 连接池最大连接数
        """
        self._connection: Optional[ConnectionBase] = None
        self._timeout = timeout
        self._use_pool = use_pool
        self._max_pool_size = max_pool_size
        self._pool: Optional[TCPConnectionPool] = None
        self._connected = False
        self._authenticated = False
        self._current_server_id: Optional[int] = None

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected and self._connection is not None

    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self._authenticated

    @property
    def current_server_id(self) -> Optional[int]:
        """当前选中的虚拟服务器ID"""
        return self._current_server_id

    async def connect(
        self,
        host: str,
        port: Optional[int] = None,
        username: str = "serveradmin",
        password: str = "",
        connection_type: ConnectionType = ConnectionType.TCP,
        ssh_username: Optional[str] = None,
        ssh_password: Optional[str] = None,
        ssh_key_filename: Optional[str] = None,
        connection_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
    ) -> None:
        """
        连接到 TeamSpeak 服务器并认证

        Args:
            host: 服务器地址
            port: 服务器端口（TCP 默认 10011，SSH 默认 10022）
            username: ServerQuery 用户名
            password: ServerQuery 密码
            connection_type: 连接类型（TCP 或 SSH）
            ssh_username: SSH 用户名（仅 SSH 连接）
            ssh_password: SSH 密码（仅 SSH 连接）
            ssh_key_filename: SSH 私钥文件路径（仅 SSH 连接）
            connection_timeout: 连接超时（aiohttp 风格，可选）
            read_timeout: 读取超时（aiohttp 风格，可选）

        Raises:
            ConnectionError: 连接失败
            AuthenticationError: 认证失败
        """
        # 断开现有连接
        if self._connected:
            await self.disconnect()

        # 创建连接
        if connection_type == ConnectionType.TCP:
            actual_port = port or TCPConnection.DEFAULT_PORT
            self._connection = TCPConnection(
                host,
                actual_port,
                self._timeout,
                connection_timeout=connection_timeout,
                read_timeout=read_timeout,
            )
        else:
            actual_port = port or SSHConnection.DEFAULT_PORT
            self._connection = SSHConnection(
                host,
                actual_port,
                self._timeout,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                ssh_key_filename=ssh_key_filename,
            )

        # 建立连接
        await self._connection.connect()
        self._connected = True

        # 执行认证
        if username and password:
            await self.login(username, password)

    async def disconnect(self) -> None:
        """
        断开连接

        退出 ServerQuery 并断开连接。
        """
        if not self._connected:
            return

        # 尝试发送 quit 命令
        try:
            await self._raw_execute("quit")
        except Exception:
            pass

        # 断开连接
        if self._connection:
            await self._connection.disconnect()
            self._connection = None

        self._connected = False
        self._authenticated = False
        self._current_server_id = None

    async def login(self, username: str, password: str) -> None:
        """
        使用 ServerQuery 凭据登录

        Args:
            username: 用户名
            password: 密码

        Raises:
            AuthenticationError: 认证失败
        """
        response = await self._raw_execute(
            "login", {"client_login_name": username, "client_login_password": password}
        )

        if not response.success:
            self._authenticated = False
            raise AuthenticationError(
                "认证失败",
                username=username,
                error_id=response.error_id,
                details={"error_msg": response.error_msg},
            )

        self._authenticated = True

    async def use_server(self, server_id: int) -> None:
        """
        选择虚拟服务器

        Args:
            server_id: 虚拟服务器 ID

        Raises:
            CommandError: 切换失败
        """
        response = await self._raw_execute("use", {"sid": server_id})

        if not response.success:
            raise CommandError(
                "切换服务器失败",
                command="use",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )

        self._current_server_id = server_id

    async def execute(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        options: Optional[List[str]] = None,
    ) -> QueryResponse:
        """
        执行 ServerQuery 命令

        Args:
            command: 命令名称
            params: 命令参数
            options: 命令选项

        Returns:
            QueryResponse 对象

        Raises:
            NotConnectedError: 未连接
            CommandError: 命令执行失败
        """
        if not self.is_connected:
            raise NotConnectedError("未连接到服务器，请先调用 connect()")

        if options:
            cmd_str = CommandEncoder.encode_command_with_options(
                command, params, options
            )
        else:
            cmd_str = CommandEncoder.encode_command(command, params)

        return await self._raw_execute(command, params, options)

    async def _raw_execute(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        options: Optional[List[str]] = None,
    ) -> QueryResponse:
        """
        执行原始命令

        Args:
            command: 命令名称
            params: 命令参数
            options: 命令选项

        Returns:
            QueryResponse 对象
        """
        if options:
            cmd_str = CommandEncoder.encode_command_with_options(
                command, params, options
            )
        else:
            cmd_str = CommandEncoder.encode_command(command, params)

        raw_response = await self._connection.send_and_receive(cmd_str)
        response = ResponseParser.parse_response(raw_response)

        return response

    # ==================== 服务器命令 ====================

    async def server_list(self) -> List[Dict[str, Any]]:
        """
        获取虚拟服务器列表

        Returns:
            服务器信息字典列表
        """
        response = await self.execute("serverlist")
        if not response.success:
            raise CommandError(
                "获取服务器列表失败",
                command="serverlist",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )
        return response.data

    async def server_info(self) -> Dict[str, Any]:
        """
        获取当前服务器详细信息

        Returns:
            服务器信息字典
        """
        response = await self.execute("serverinfo")
        if not response.success:
            raise CommandError(
                "获取服务器信息失败",
                command="serverinfo",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )
        return response.first or {}

    async def version(self) -> Dict[str, Any]:
        """
        获取服务器版本信息

        Returns:
            版本信息字典
        """
        response = await self.execute("version")
        if not response.success:
            raise CommandError(
                "获取版本信息失败",
                command="version",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )
        return response.first or {}

    async def host_info(self) -> Dict[str, Any]:
        """
        获取主机信息

        Returns:
            主机信息字典
        """
        response = await self.execute("hostinfo")
        if not response.success:
            raise CommandError(
                "获取主机信息失败",
                command="hostinfo",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )
        return response.first or {}

    # ==================== 用户命令 ====================

    async def client_list(
        self,
        uid: bool = False,
        away: bool = False,
        voice: bool = False,
        times: bool = False,
        groups: bool = False,
        info: bool = False,
        country: bool = False,
        ip: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        获取在线用户列表

        Args:
            uid: 包含唯一标识符
            away: 包含离开状态
            voice: 包含语音信息
            times: 包含连接时间
            groups: 包含服务器组信息
            info: 包含额外信息
            country: 包含国家信息
            ip: 包含 IP 地址

        Returns:
            用户信息字典列表
        """
        options = []
        if uid:
            options.append("uid")
        if away:
            options.append("away")
        if voice:
            options.append("voice")
        if times:
            options.append("times")
        if groups:
            options.append("groups")
        if info:
            options.append("info")
        if country:
            options.append("country")
        if ip:
            options.append("ip")

        response = await self.execute("clientlist", options=options if options else None)
        if not response.success:
            raise CommandError(
                "获取用户列表失败",
                command="clientlist",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )
        return response.data

    async def client_info(self, client_id: int) -> Dict[str, Any]:
        """
        获取用户详细信息

        Args:
            client_id: 客户端 ID

        Returns:
            用户详细信息字典
        """
        response = await self.execute("clientinfo", {"clid": client_id})
        if not response.success:
            raise CommandError(
                "获取用户信息失败",
                command="clientinfo",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )
        return response.first or {}

    async def client_move(self, client_id: int, channel_id: int) -> None:
        """
        移动用户到其他频道

        Args:
            client_id: 客户端 ID
            channel_id: 目标频道 ID

        Raises:
            CommandError: 移动失败
        """
        response = await self.execute("clientmove", {"clid": client_id, "cid": channel_id})
        if not response.success:
            raise CommandError(
                "移动用户失败",
                command="clientmove",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )

    async def client_kick(
        self,
        client_id: int,
        reason_id: int = 5,
        reason_msg: str = ""
    ) -> None:
        """
        踢出用户

        Args:
            client_id: 客户端 ID
            reason_id: 踢出原因 ID
                - 4: 踢出频道
                - 5: 踢出服务器
            reason_msg: 踢出原因消息

        Raises:
            CommandError: 踢出失败
        """
        params = {"clid": client_id, "reasonid": reason_id}
        if reason_msg:
            params["reasonmsg"] = reason_msg

        response = await self.execute("clientkick", params)
        if not response.success:
            raise CommandError(
                "踢出用户失败",
                command="clientkick",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )

    async def ban_add(
        self,
        ip: Optional[str] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
        duration: int = 0,
        reason: str = ""
    ) -> int:
        """
        添加封禁

        Args:
            ip: 要封禁的 IP 地址
            name: 要封禁的用户名
            uid: 要封禁的唯一标识符
            duration: 封禁时长（秒），0 表示永久
            reason: 封禁原因

        Returns:
            封禁 ID

        Raises:
            CommandError: 添加封禁失败
        """
        params = {}
        if ip:
            params["ip"] = ip
        if name:
            params["name"] = name
        if uid:
            params["uid"] = uid
        if duration > 0:
            params["duration"] = duration
        if reason:
            params["reason"] = reason

        response = await self.execute("banadd", params)
        if not response.success:
            raise CommandError(
                "添加封禁失败",
                command="banadd",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )

        # 返回封禁 ID
        if response.first:
            return response.first.get("banid", 0)
        return 0

    async def ban_list(self) -> List[Dict[str, Any]]:
        """
        获取封禁列表

        Returns:
            封禁条目字典列表
        """
        response = await self.execute("banlist")
        if not response.success:
            raise CommandError(
                "获取封禁列表失败",
                command="banlist",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )
        return response.data

    async def ban_delete(self, ban_id: int) -> None:
        """
        删除封禁

        Args:
            ban_id: 封禁 ID

        Raises:
            CommandError: 删除封禁失败
        """
        response = await self.execute("bandel", {"banid": ban_id})
        if not response.success:
            raise CommandError(
                "删除封禁失败",
                command="bandel",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )

    # ==================== 上下文管理器 ====================

    async def __aenter__(self) -> "TS6QueryClient":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.disconnect()

    def __repr__(self) -> str:
        status = "已连接" if self._connected else "未连接"
        auth = "已认证" if self._authenticated else "未认证"
        return f"<TS6QueryClient {status} {auth}>"
