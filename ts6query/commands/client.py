"""
用户命令封装
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import TS6QueryClient

from ..models.user import UserInfo, ClientListEntry, BanEntry


class ClientCommands:
    """用户命令封装类"""

    def __init__(self, client: "TS6QueryClient"):
        """
        初始化用户命令

        Args:
            client: TS6QueryClient 实例
        """
        self._client = client

    async def list(
        self,
        uid: bool = False,
        away: bool = False,
        voice: bool = False,
        times: bool = False,
        groups: bool = False,
        info: bool = False,
        country: bool = False,
    ) -> List[ClientListEntry]:
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

        Returns:
            ClientListEntry 列表
        """
        data = await self._client.client_list(
            uid=uid, away=away, voice=voice, times=times, groups=groups, info=info, country=country
        )
        return [ClientListEntry(**item) for item in data]

    async def info(self, client_id: int) -> UserInfo:
        """
        获取用户详细信息

        Args:
            client_id: 客户端 ID

        Returns:
            UserInfo 对象
        """
        data = await self._client.client_info(client_id)
        return UserInfo(**data)

    async def move(self, client_id: int, channel_id: int) -> None:
        """
        移动用户到其他频道

        Args:
            client_id: 客户端 ID
            channel_id: 目标频道 ID
        """
        await self._client.client_move(client_id, channel_id)

    async def kick(
        self,
        client_id: int,
        from_server: bool = True,
        reason: str = ""
    ) -> None:
        """
        踢出用户

        Args:
            client_id: 客户端 ID
            from_server: True 为踢出服务器，False 为踢出频道
            reason: 踢出原因
        """
        reason_id = 5 if from_server else 4
        await self._client.client_kick(client_id, reason_id, reason)

    async def kick_from_channel(self, client_id: int, reason: str = "") -> None:
        """
        将用户踢出当前频道

        Args:
            client_id: 客户端 ID
            reason: 踢出原因
        """
        await self.kick(client_id, from_server=False, reason=reason)

    async def kick_from_server(self, client_id: int, reason: str = "") -> None:
        """
        将用户踢出服务器

        Args:
            client_id: 客户端 ID
            reason: 踢出原因
        """
        await self.kick(client_id, from_server=True, reason=reason)

    async def ban(
        self,
        client_id: Optional[int] = None,
        ip: Optional[str] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
        duration: int = 0,
        reason: str = ""
    ) -> int:
        """
        封禁用户

        Args:
            client_id: 客户端 ID（可选，用于自动获取信息）
            ip: IP 地址
            name: 用户名
            uid: 唯一标识符
            duration: 封禁时长（秒），0 表示永久
            reason: 封禁原因

        Returns:
            封禁 ID
        """
        # 如果提供了 client_id，获取用户信息
        if client_id and not (ip or name or uid):
            user_info = await self.info(client_id)
            ip = ip or getattr(user_info, "connection_client_ip", None)
            name = name or user_info.client_nickname
            uid = uid or user_info.client_unique_identifier

        return await self._client.ban_add(ip=ip, name=name, uid=uid, duration=duration, reason=reason)

    async def ban_list(self) -> List[BanEntry]:
        """
        获取封禁列表

        Returns:
            BanEntry 列表
        """
        data = await self._client.ban_list()
        return [BanEntry(**item) for item in data]

    async def unban(self, ban_id: int) -> None:
        """
        解除封禁

        Args:
            ban_id: 封禁 ID
        """
        await self._client.ban_delete(ban_id)

    async def find_by_name(self, nickname: str) -> Optional[ClientListEntry]:
        """
        根据用户名查找用户

        Args:
            nickname: 用户名

        Returns:
            找到的 ClientListEntry，未找到返回 None
        """
        clients = await self.list()
        for client in clients:
            if client.client_nickname.lower() == nickname.lower():
                return client
        return None

    async def find_by_uid(self, uid: str) -> Optional[ClientListEntry]:
        """
        根据唯一标识符查找用户

        Args:
            uid: 唯一标识符

        Returns:
            找到的 ClientListEntry，未找到返回 None
        """
        clients = await self.list(uid=True)
        for client in clients:
            if client.client_unique_identifier == uid:
                return client
        return None

    async def get_voice_clients(self) -> List[ClientListEntry]:
        """
        获取所有语音客户端（排除 ServerQuery 客户端）

        Returns:
            语音客户端列表
        """
        clients = await self.list()
        return [c for c in clients if c.is_voice_client]

    async def get_query_clients(self) -> List[ClientListEntry]:
        """
        获取所有 ServerQuery 客户端

        Returns:
            ServerQuery 客户端列表
        """
        clients = await self.list()
        return [c for c in clients if c.is_query_client]

    async def get_away_clients(self) -> List[ClientListEntry]:
        """
        获取所有离开状态的用户

        Returns:
            离开状态的用户列表
        """
        clients = await self.list(away=True)
        return [c for c in clients if c.is_away]
