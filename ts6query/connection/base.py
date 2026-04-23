"""
连接抽象基类
"""

from abc import ABC, abstractmethod
from typing import Optional
import asyncio


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
        self.timeout = timeout
        self.encoding = encoding
        self._connected = False
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()

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

        try:
            data = await asyncio.wait_for(
                self._reader.readline(), timeout=self.timeout
            )
            return data.decode(self.encoding).strip()
        except asyncio.TimeoutError:
            raise TimeoutError(
                "接收数据超时",
                timeout_seconds=self.timeout,
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
