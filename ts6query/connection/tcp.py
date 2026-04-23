"""
TCP 连接实现
"""

import asyncio
from typing import Optional
from .base import ConnectionBase
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
    ):
        """
        初始化 TCP 连接

        Args:
            host: TeamSpeak 服务器地址
            port: ServerQuery 端口（默认 10011）
            timeout: 超时时间
            encoding: 字符编码
        """
        super().__init__(host, port, timeout, encoding)
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

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
            self._connected = True

            # 读取欢迎消息
            # TeamSpeak 通常发送两行欢迎消息
            # 第一行：TS3
            # 第二行：欢迎消息
            welcome_lines = []
            for _ in range(2):
                try:
                    line = await asyncio.wait_for(
                        self._reader.readline(), timeout=self.timeout
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
                details={"timeout": self.timeout},
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
