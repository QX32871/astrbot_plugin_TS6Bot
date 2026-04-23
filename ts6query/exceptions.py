"""
ts6query 异常定义

定义库中使用的所有异常类。
"""

from typing import Optional, Any

#ts6query 基础异常类
class TS6QueryError(Exception):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message

#连接相关异常
class ConnectionError(TS6QueryError):
    def __init__(
        self,
        message: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message, details)
        self.host = host
        self.port = port

    def __str__(self) -> str:
        base = super().__str__()
        if self.host and self.port:
            return f"{base} (连接到 {self.host}:{self.port})"
        return base

#认证失败异常
class AuthenticationError(TS6QueryError):
    def __init__(
        self,
        message: str = "认证失败",
        username: Optional[str] = None,
        error_id: Optional[int] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message, details)
        self.username = username
        self.error_id = error_id

#命令执行异常
class CommandError(TS6QueryError):
    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        error_id: Optional[int] = None,
        error_msg: Optional[str] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message, details)
        self.command = command
        self.error_id = error_id
        self.error_msg = error_msg

    def __str__(self) -> str:
        base = self.message
        if self.command:
            base = f"[{self.command}] {base}"
        if self.error_id is not None:
            base = f"{base} (错误ID: {self.error_id})"
        if self.error_msg:
            base = f"{base}: {self.error_msg}"
        return base


#响应解析异常
class ParseError(TS6QueryError):
    def __init__(
        self,
        message: str,
        raw_data: Optional[str] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message, details)
        self.raw_data = raw_data

    def __str__(self) -> str:
        base = self.message
        if self.raw_data:
            truncated = self.raw_data[:100] + "..." if len(self.raw_data) > 100 else self.raw_data
            base = f"{base} (原始数据: {truncated})"
        return base

#超时异常
class TimeoutError(TS6QueryError):
    def __init__(
        self,
        message: str = "操作超时",
        timeout_seconds: Optional[float] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds

    def __str__(self) -> str:
        base = self.message
        if self.timeout_seconds is not None:
            base = f"{base} ({self.timeout_seconds}秒)"
        return base

#未连接异常
class NotConnectedError(TS6QueryError):
    def __init__(self, message: str = "未连接到服务器"):
        super().__init__(message)
