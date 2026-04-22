"""ts6query 数据模型"""

from ts6query.models.server import ServerInfo, VirtualServerInfo
from ts6query.models.user import UserInfo, ClientListEntry

__all__ = ["ServerInfo", "VirtualServerInfo", "UserInfo", "ClientListEntry"]
