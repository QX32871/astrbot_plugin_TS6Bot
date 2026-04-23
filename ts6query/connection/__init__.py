"""ts6query 连接模块"""

from ts6query.connection.base import ConnectionBase
from ts6query.connection.tcp import TCPConnection
from ts6query.connection.ssh import SSHConnection

__all__ = ["ConnectionBase", "TCPConnection", "SSHConnection"]
