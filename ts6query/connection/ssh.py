"""
SSH 连接实现

通过 SSH 协议连接到 TeamSpeak ServerQuery。
TeamSpeak 6 支持 SSH 方式的 ServerQuery（默认端口 10022）。
"""

import asyncio
from typing import Optional
from .base import ConnectionBase
from ..exceptions import ConnectionError as TS6ConnectionError

# 尝试导入 paramiko，如果不可用则设置标志
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class SSHConnection(ConnectionBase):
    """SSH 连接实现"""

    # TeamSpeak ServerQuery SSH 默认端口
    DEFAULT_PORT = 10022

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = 10.0,
        encoding: str = "utf-8",
        ssh_username: Optional[str] = None,
        ssh_password: Optional[str] = None,
        ssh_key_filename: Optional[str] = None,
    ):
        """
        初始化 SSH 连接

        Args:
            host: TeamSpeak 服务器地址
            port: ServerQuery SSH 端口（默认 10022）
            timeout: 超时时间
            encoding: 字符编码
            ssh_username: SSH 用户名（可选，用于 SSH 认证）
            ssh_password: SSH 密码（可选）
            ssh_key_filename: SSH 私钥文件路径（可选）
        """
        super().__init__(host, port, timeout, encoding)
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_key_filename = ssh_key_filename
        self._client: Optional[paramiko.SSHClient] = None
        self._channel: Optional[paramiko.Channel] = None
        self._welcome_message: Optional[str] = None

    async def connect(self) -> None:
        """
        建立 SSH 连接

        Raises:
            ConnectionError: 连接失败
            ImportError: paramiko 库未安装
        """
        if not PARAMIKO_AVAILABLE:
            raise ImportError(
                "SSH 连接需要安装 paramiko 库。请运行: pip install paramiko"
            )

        if self._connected:
            return

        try:
            # 在单独的线程中执行阻塞的 SSH 连接
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connect_ssh)

            self._connected = True

            # 读取欢迎消息
            self._welcome_message = await self._read_welcome()

        except Exception as e:
            self._cleanup()
            raise TS6ConnectionError(
                f"SSH 连接失败: {e}",
                host=self.host,
                port=self.port,
                details={"exception": str(e)},
            )

    def _connect_ssh(self) -> None:
        """执行阻塞的 SSH 连接"""
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.host,
            "port": self.port,
            "timeout": self.timeout,
            "look_for_keys": False,
            "allow_agent": False,
        }

        if self.ssh_username:
            connect_kwargs["username"] = self.ssh_username
        else:
            connect_kwargs["username"] = "serveradmin"

        if self.ssh_password:
            connect_kwargs["password"] = self.ssh_password

        if self.ssh_key_filename:
            connect_kwargs["key_filename"] = self.ssh_key_filename

        self._client.connect(**connect_kwargs)

        # 创建交互式 shell
        self._channel = self._client.invoke_shell()
        self._channel.settimeout(self.timeout)

    async def _read_welcome(self) -> str:
        """读取欢迎消息"""
        lines = []
        loop = asyncio.get_event_loop()

        for _ in range(2):
            try:
                line = await asyncio.wait_for(
                    loop.run_in_executor(None, self._readline),
                    timeout=self.timeout,
                )
                if line:
                    lines.append(line)
            except asyncio.TimeoutError:
                break

        return "\n".join(lines)

    def _readline(self) -> str:
        """阻塞式读取一行"""
        if not self._channel:
            return ""

        line = b""
        while True:
            char = self._channel.recv(1)
            if not char:
                break
            line += char
            if char == b"\n":
                break

        return line.decode(self.encoding).strip()

    def _read_until(self, delimiter: str = "error") -> str:
        """阻塞式读取直到遇到 delimiter"""
        lines = []
        while True:
            line = self._readline()
            lines.append(line)
            if line.startswith(delimiter):
                break
        return "\n".join(lines)

    async def disconnect(self) -> None:
        """断开 SSH 连接"""
        if not self._connected:
            return

        self._connected = False
        self._cleanup()

    def _cleanup(self) -> None:
        """清理资源"""
        if self._channel:
            try:
                self._channel.close()
            except Exception:
                pass
            finally:
                self._channel = None

        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            finally:
                self._client = None

    async def send(self, data: str) -> None:
        """发送数据"""
        if not self._connected or not self._channel:
            raise TS6ConnectionError(
                "未连接到服务器", host=self.host, port=self.port
            )

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None, self._channel.send, (data + "\n").encode(self.encoding)
            )
        except Exception as e:
            raise TS6ConnectionError(
                f"发送数据失败: {e}",
                host=self.host,
                port=self.port,
                details={"exception": str(e)},
            )

    async def receive(self) -> str:
        """接收数据"""
        if not self._connected or not self._channel:
            raise TS6ConnectionError(
                "未连接到服务器", host=self.host, port=self.port
            )

        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._readline),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            from ..exceptions import TimeoutError
            raise TimeoutError(
                "接收数据超时",
                timeout_seconds=self.timeout,
                details={"host": self.host, "port": self.port},
            )

    async def receive_until(self, delimiter: str = "error") -> str:
        """接收数据直到遇到指定行"""
        if not self._connected or not self._channel:
            raise TS6ConnectionError(
                "未连接到服务器", host=self.host, port=self.port
            )

        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._read_until, delimiter),
                timeout=self.timeout * 5,  # 给更长超时时间
            )
        except asyncio.TimeoutError:
            from ..exceptions import TimeoutError
            raise TimeoutError(
                "接收响应超时",
                timeout_seconds=self.timeout * 5,
                details={"host": self.host, "port": self.port},
            )

    @property
    def welcome_message(self) -> Optional[str]:
        """获取欢迎消息"""
        return self._welcome_message

    def __repr__(self) -> str:
        status = "已连接" if self._connected else "未连接"
        return f"<SSHConnection {self.host}:{self.port} ({status})>"
