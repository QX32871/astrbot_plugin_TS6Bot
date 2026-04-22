"""
服务器命令封装
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import TS6QueryClient

from ..models.server import ServerInfo, VirtualServerInfo, HostInfo, VersionInfo


class ServerCommands:
    """服务器命令封装类"""

    def __init__(self, client: "TS6QueryClient"):
        """
        初始化服务器命令

        Args:
            client: TS6QueryClient 实例
        """
        self._client = client

    async def list(self) -> List[VirtualServerInfo]:
        """
        获取虚拟服务器列表

        Returns:
            VirtualServerInfo 列表
        """
        data = await self._client.server_list()
        return [VirtualServerInfo(**item) for item in data]

    async def info(self) -> ServerInfo:
        """
        获取当前服务器详细信息

        Returns:
            ServerInfo 对象
        """
        data = await self._client.server_info()
        return ServerInfo(**data)

    async def version(self) -> VersionInfo:
        """
        获取服务器版本信息

        Returns:
            VersionInfo 对象
        """
        data = await self._client.version()
        return VersionInfo(
            version=data.get("version", ""),
            build=data.get("build", 0),
            platform=data.get("platform", ""),
        )

    async def host_info(self) -> HostInfo:
        """
        获取主机信息

        Returns:
            HostInfo 对象
        """
        data = await self._client.host_info()
        return HostInfo(**data)

    async def use(self, server_id: int) -> None:
        """
        选择虚拟服务器

        Args:
            server_id: 虚拟服务器 ID
        """
        await self._client.use_server(server_id)

    async def start(self, server_id: int) -> None:
        """
        启动虚拟服务器

        Args:
            server_id: 虚拟服务器 ID
        """
        response = await self._client.execute("serverstart", {"sid": server_id})
        if not response.success:
            from ..exceptions import CommandError
            raise CommandError(
                "启动服务器失败",
                command="serverstart",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )

    async def stop(self, server_id: int, reason: str = "") -> None:
        """
        停止虚拟服务器

        Args:
            server_id: 虚拟服务器 ID
            reason: 停止原因
        """
        params = {"sid": server_id}
        if reason:
            params["reasonmsg"] = reason

        response = await self._client.execute("serverstop", params)
        if not response.success:
            from ..exceptions import CommandError
            raise CommandError(
                "停止服务器失败",
                command="serverstop",
                error_id=response.error_id,
                error_msg=response.error_msg,
            )

    async def get_clients_online(self) -> int:
        """
        获取当前在线用户数

        Returns:
            在线用户数
        """
        info = await self.info()
        return info.virtualserver_clients_online

    async def get_max_clients(self) -> int:
        """
        获取最大用户数

        Returns:
            最大用户数
        """
        info = await self.info()
        return info.virtualserver_max_clients

    async def get_uptime(self) -> str:
        """
        获取服务器运行时间

        Returns:
            人类可读的运行时间字符串
        """
        info = await self.info()
        return info.uptime_human
