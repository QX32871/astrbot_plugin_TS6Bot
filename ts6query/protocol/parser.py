"""
响应解析器

解析 TeamSpeak ServerQuery 协议响应。
"""

import re
from typing import Dict, Any, Optional

from .types import QueryResponse, UNESCAPE_MAP


# ServerQuery 响应解析器
class ResponseParser:
    # 错误行正则：error id=X msg=Y
    ERROR_PATTERN = re.compile(r"^error id=(\d+)\s+msg=([^\r\n]*)$")

    # 反转义字符串，将 TeamSpeak 转义序列转换回原始字符。
    @staticmethod
    def unescape(value: str) -> str:
        result = value
        for escaped, char in UNESCAPE_MAP.items():
            result = result.replace(escaped, char)
        return result

    # 解析值为 Python 类型，尝试将字符串值转换为适当的 Python 类型。
    @staticmethod
    def parse_value(value: str) -> Any:
        if not value:
            return ""

        # 反转义
        unescaped = ResponseParser.unescape(value)

        # 尝试转换为数字
        try:
            if "." in unescaped:
                return float(unescaped)
            return int(unescaped)
        except ValueError:
            pass

        # 布尔值处理（TeamSpeak 使用 0/1）
        if unescaped == "0":
            return False
        elif unescaped == "1":
            return True
        return unescaped

    """
    解析键值对字符串

    格式：key1=value1 key2=value2 ...

    Args:
        data: 键值对字符串

    Returns:
        解析后的字典
    """

    @staticmethod
    def parse_key_value_pairs(data: str) -> Dict[str, Any]:
        result = {}
        if not data:
            return result

        # 按空格分割键值对，注意处理转义的空格
        pairs = []
        current = ""
        i = 0
        while i < len(data):
            if data[i] == "\\" and i + 1 < len(data):
                # 转义字符，直接添加
                current += data[i: i + 2]
                i += 2
            elif data[i] == " ":
                # 空格分隔符
                if current:
                    pairs.append(current)
                current = ""
                i += 1
            else:
                current += data[i]
                i += 1
        if current:
            pairs.append(current)

        # 解析每个键值对
        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                result[key] = ResponseParser.parse_value(value)
            else:
                # 无值的键（通常是选项）
                result[pair] = True
        return result

    """
    解析单个响应行

    Args:
        line: 响应行

    Returns:
        解析后的字典
    """

    @staticmethod
    def parse_response_line(line: str) -> Dict[str, Any]:
        return ResponseParser.parse_key_value_pairs(line)

    """
    解析完整响应

    TeamSpeak ServerQuery 响应格式：
    - 数据行（可选）：key1=value1 key2=value2 ...
    - 多数据项用 | 分隔
    - 错误行：error id=X msg=Y

    Args:
        raw_response: 原始响应字符串

    Returns:
        QueryResponse 对象
    """

    @staticmethod
    def parse_response(raw_response: str) -> QueryResponse:
        if not raw_response:
            return QueryResponse(
                success=False, error_id=-1, error_msg="空响应", raw_response=raw_response
            )
        lines = raw_response.strip().split("\n")
        data_lines = []
        error_line = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = ResponseParser.ERROR_PATTERN.match(line)
            if match:
                error_line = line
            else:
                data_lines.append(line)

        # 解析错误行
        if error_line:
            match = ResponseParser.ERROR_PATTERN.match(error_line)
            if match:
                error_id = int(match.group(1))
                error_msg = ResponseParser.unescape(match.group(2))
            else:
                error_id = -1
                error_msg = "未知错误格式"
        else:
            error_id = -1
            error_msg = "未找到错误行"

        # 解析数据行
        data = []
        for data_line in data_lines:
            # 按 | 分隔多条数据
            items = data_line.split("|")
            for item in items:
                if item.strip():
                    parsed = ResponseParser.parse_response_line(item)
                    if parsed:
                        data.append(parsed)
        return QueryResponse(
            success=error_id == 0,
            error_id=error_id,
            error_msg=error_msg,
            data=data,
            raw_response=raw_response,
        )

    """
    解析通知事件

    TeamSpeak 通知事件格式：
    notify<eventname> key1=value1 key2=value2 ...

    Args:
        raw_event: 原始事件字符串

    Returns:
        解析后的事件字典，包含 event_name 和 data
    """

    @staticmethod
    def parse_event(raw_event: str) -> Optional[Dict[str, Any]]:
        if not raw_event or not raw_event.startswith("notify"):
            return None
        parts = raw_event.split(" ", 1)
        event_name = parts[0]
        data = {}
        if len(parts) > 1:
            data = ResponseParser.parse_key_value_pairs(parts[1])
        return {
            "event_name": event_name,
            "data": data,
        }
