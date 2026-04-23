"""
连接抽象基类

使用 aiohttp 风格的超时控制和连接管理。
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
import asyncio


@dataclass
class ConnectionTimeout:
    """连接超时配置（aiohttp 风格）"""
    total: Optional[float] = None
    connect: Optional[float] = None
    sock_read: Optional[float] = None
    sock_connect: Optional[float] = None

    @classmethod
    def from_float(cls, timeout: float) -> "ConnectionTimeout":
        """从单一超时值创建配置"""
        return cls(total=timeout, connect=timeout, sock_read=timeout)


class ConnectionBase(ABC):
    """连接抽象基类"""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 10.0,
        encoding: str = "utf-8",
    ):
        """
        初始化连接基类

        Args:
            host: 服务器地址
            port: 服务器端口
            timeout: 连接和操作超时时间（秒）
            encoding: 字符编码
        """
        self.host = host
        self.port = port
        self._timeout = timeout
        self.encoding = encoding
        self._connected = False
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()

        # aiohttp 风格的超时配置
        self._timeout_config = ConnectionTimeout.from_float(timeout)

    @property
    def timeout(self) -> float:
        """获取默认超时时间"""
        return self._timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        """设置默认超时时间"""
        self._timeout = value
        self._timeout_config = ConnectionTimeout.from_float(value)

    @property
    def timeout_config(self) -> ConnectionTimeout:
        """获取超时配置"""
        return self._timeout_config

    @timeout_config.setter
    def timeout_config(self, value: ConnectionTimeout) -> None:
        """设置超时配置"""
        self._timeout_config = value
        self._timeout = value.total or 10.0

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @abstractmethod
    async def connect(self) -> None:
        """
        建立连接

        Raises:
            ConnectionError: 连接失败
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        断开连接
        """
        pass

    async def send(self, data: str) -> None:
        """
        发送数据

        Args:
            data: 要发送的字符串数据

        Raises:
            ConnectionError: 未连接或发送失败
        """
        if not self._connected or self._writer is None:
            raise ConnectionError(
                "未连接到服务器", host=self.host, port=self.port
            )

        async with self._lock:
            try:
                self._writer.write((data + "\n").encode(self.encoding))
                await self._writer.drain()
            except Exception as e:
                raise ConnectionError(
                    f"发送数据失败: {e}",
                    host=self.host,
                    port=self.port,
                    details={"exception": str(e)},
                )

    async def receive(self) -> str:
        """
        接收数据

        Returns:
            接收到的字符串数据

        Raises:
            ConnectionError: 未连接或接收失败
            TimeoutError: 接收超时
        """
        if not self._connected or self._reader is None:
            raise ConnectionError(
                "未连接到服务器", host=self.host, port=self.port
            )

        timeout_val = self._timeout_config.sock_read or self._timeout
        try:
            data = await asyncio.wait_for(
                self._reader.readline(), timeout=timeout_val
            )
            return data.decode(self.encoding).strip()
        except asyncio.TimeoutError:
            raise TimeoutError(
                "接收数据超时",
                timeout_seconds=timeout_val,
                details={"host": self.host, "port": self.port},
            )
        except Exception as e:
            raise ConnectionError(
                f"接收数据失败: {e}",
                host=self.host,
                port=self.port,
                details={"exception": str(e)},
            )

    async def receive_until(self, delimiter: str = "error") -> str:
        """
        接收数据直到遇到包含指定内容的行

        ServerQuery 响应以 "error id=X msg=Y" 结尾

        Args:
            delimiter: 结束标记

        Returns:
            完整的响应字符串
        """
        lines = []
        while True:
            line = await self.receive()
            lines.append(line)
            if line.startswith(delimiter):
                break

        return "\n".join(lines)

    async def send_and_receive(self, data: str) -> str:
        """
        发送数据并等待响应

        Args:
            data: 要发送的命令

        Returns:
            响应字符串
        """
        await self.send(data)
        return await self.receive_until("error")

    async def __aenter__(self) -> "ConnectionBase":
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.disconnect()
