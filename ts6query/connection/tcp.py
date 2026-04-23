"""
TCP 连接实现

使用asyncio实现连接管理和超时控制。
"""

import asyncio
from typing import Optional
from .base import ConnectionBase, ConnectionTimeout
from ..exceptions import ConnectionError as TS6ConnectionError


class TCPConnection(ConnectionBase):
    """TCP 连接实现"""

    # TeamSpeak ServerQuery 默认端口
    DEFAULT_PORT = 10011

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = 10.0,
        encoding: str = "utf-8",
        connection_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
    ):
        """
        初始化 TCP 连接

        Args:
            host: TeamSpeak 服务器地址
            port: ServerQuery 端口（默认 10011）
            timeout: 默认超时时间
            encoding: 字符编码
            connection_timeout: 连接超时（单独设置，aiohttp 风格）
            read_timeout: 读取超时（单独设置，aiohttp 风格）
        """
        super().__init__(host, port, timeout, encoding)

        # aiohttp 风格的细粒度超时控制
        if connection_timeout is not None or read_timeout is not None:
            self._timeout_config = ConnectionTimeout(
                total=timeout,
                connect=connection_timeout or timeout,
                sock_read=read_timeout or timeout,
                sock_connect=connection_timeout or timeout,
            )

        self._welcome_message: Optional[str] = None

    async def connect(self) -> None:
        """
        建立 TCP 连接

        连接后会读取欢迎消息。

        Raises:
            ConnectionError: 连接失败
        """
        if self._connected:
            return

        connect_timeout = self._timeout_config.sock_connect or self._timeout

        try:
            # 使用 aiohttp 风格的连接超时
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=connect_timeout,
            )
            self._connected = True

            # 读取欢迎消息
            # TeamSpeak 通常发送两行欢迎消息
            # 第一行：TS3
            # 第二行：欢迎消息
            welcome_lines = []
            read_timeout = self._timeout_config.sock_read or self._timeout

            for _ in range(2):
                try:
                    line = await asyncio.wait_for(
                        self._reader.readline(), timeout=read_timeout
                    )
                    welcome_lines.append(line.decode(self.encoding).strip())
                except asyncio.TimeoutError:
                    break

            self._welcome_message = "\n".join(welcome_lines)

        except asyncio.TimeoutError:
            raise TS6ConnectionError(
                "连接超时",
                host=self.host,
                port=self.port,
                details={"timeout": connect_timeout},
            )
        except OSError as e:
            raise TS6ConnectionError(
                f"连接失败: {e}",
                host=self.host,
                port=self.port,
                details={"exception": str(e)},
            )
        except Exception as e:
            raise TS6ConnectionError(
                f"连接时发生错误: {e}",
                host=self.host,
                port=self.port,
                details={"exception": str(e)},
            )

    async def disconnect(self) -> None:
        """
        断开 TCP 连接
        """
        if not self._connected:
            return

        self._connected = False

        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            finally:
                self._writer = None

        self._reader = None

    @property
    def welcome_message(self) -> Optional[str]:
        """获取连接时的欢迎消息"""
        return self._welcome_message

    def __repr__(self) -> str:
        status = "已连接" if self._connected else "未连接"
        return f"<TCPConnection {self.host}:{self.port} ({status})>"


class TCPConnectionPool:
    """TCP 连接池（aiohttp 风格）"""

    def __init__(
        self,
        host: str,
        port: int = TCPConnection.DEFAULT_PORT,
        timeout: float = 10.0,
        max_connections: int = 10,
        encoding: str = "utf-8",
    ):
        """
        初始化连接池

        Args:
            host: 服务器地址
            port: 服务器端口
            timeout: 默认超时时间
            max_connections: 最大连接数
            encoding: 字符编码
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_connections = max_connections
        self.encoding = encoding

        self._pool: list[TCPConnection] = []
        self._in_use: set[TCPConnection] = set()
        self._lock = asyncio.Lock()
        self._closed = False

    async def acquire(self) -> TCPConnection:
        """
        获取一个连接

        如果池中有可用连接则复用，否则创建新连接。

        Returns:
            TCP 连接实例

        Raises:
            TS6ConnectionError: 无法获取连接
        """
        if self._closed:
            raise TS6ConnectionError(
                "连接池已关闭",
                host=self.host,
                port=self.port,
            )

        async with self._lock:
            # 尝试复用池中的连接
            while self._pool:
                conn = self._pool.pop()
                if conn.is_connected:
                    self._in_use.add(conn)
                    return conn
                else:
                    # 连接已断开，丢弃
                    pass

            # 检查是否达到最大连接数
            if len(self._in_use) >= self.max_connections:
                raise TS6ConnectionError(
                    f"连接池已满（最大 {self.max_connections} 个连接）",
                    host=self.host,
                    port=self.port,
                )

            # 创建新连接
            conn = TCPConnection(
                self.host,
                self.port,
                self.timeout,
                self.encoding,
            )
            await conn.connect()
            self._in_use.add(conn)
            return conn

    async def release(self, conn: TCPConnection) -> None:
        """
        释放连接回池中

        Args:
            conn: 要释放的连接
        """
        async with self._lock:
            if conn in self._in_use:
                self._in_use.discard(conn)

                if conn.is_connected and not self._closed:
                    self._pool.append(conn)
                else:
                    # 连接已断开或池已关闭，直接关闭连接
                    try:
                        await conn.disconnect()
                    except Exception:
                        pass

    async def close(self) -> None:
        """关闭连接池，释放所有连接"""
        async with self._lock:
            self._closed = True

            # 关闭池中的连接
            for conn in self._pool:
                try:
                    await conn.disconnect()
                except Exception:
                    pass
            self._pool.clear()

            # 关闭正在使用的连接
            for conn in list(self._in_use):
                try:
                    await conn.disconnect()
                except Exception:
                    pass
            self._in_use.clear()

    async def __aenter__(self) -> "TCPConnectionPool":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close()

    def __repr__(self) -> str:
        return (
            f"<TCPConnectionPool {self.host}:{self.port} "
            f"pool={len(self._pool)} in_use={len(self._in_use)}>"
        )
