"""
协议类型定义
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# TeamSpeak ServerQuery 协议报文中的转义字符映射
ESCAPE_MAP = {
    "\\": "\\\\",
    "/": "\\/",
    " ": "\\s",
    "|": "\\p",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
    "\v": "\\v",
    "\f": "\\f",
}

UNESCAPE_MAP = {v: k for k, v in ESCAPE_MAP.items()}


class ConnectionType(Enum):
    """连接类型"""
    TCP = "tcp"
    SSH = "ssh"


@dataclass
class QueryResponse:
    """ServerQuery 响应"""
    success: bool
    error_id: int
    error_msg: str
    data: List[Dict[str, Any]] = field(default_factory=list)
    raw_response: str = ""

    @property
    def first(self) -> Optional[Dict[str, Any]]:
        """返回第一个数据项，如果没有数据则返回 None"""
        return self.data[0] if self.data else None

    @property
    def has_data(self) -> bool:
        """是否有数据"""
        return len(self.data) > 0


@dataclass
class CommandResult:
    """命令执行结果"""
    response: QueryResponse
    command: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
