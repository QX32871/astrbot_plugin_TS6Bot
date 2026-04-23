"""
ts6query - TeamSpeak 6 ServerQuery 协议封装库

一个异步的 TeamSpeak ServerQuery 客户端库，支持 TCP 和 SSH 连接。
"""

from ts6query.client import TS6QueryClient
from ts6query.exceptions import (
    TS6QueryError,
    ConnectionError,
    AuthenticationError,
    CommandError,
    ParseError,
)
from ts6query.protocol.types import ConnectionType

__version__ = "1.0.0"
__author__ = "QX32871"

__all__ = [
    "TS6QueryClient",
    "TS6QueryError",
    "ConnectionError",
    "AuthenticationError",
    "CommandError",
    "ParseError",
    "ConnectionType",
]
