"""
命令编码器

将 Python 参数转换为 TeamSpeak ServerQuery 协议格式。
"""

from typing import Any, Dict, List, Optional, Union
from .types import ESCAPE_MAP


class CommandEncoder:
    """ServerQuery 命令编码器"""

    @staticmethod
    def escape(value: str) -> str:
        """
        转义字符串中的特殊字符

        TeamSpeak ServerQuery 协议需要转义以下字符：
        \\ / 空格 | 换行 回车 制表符 垂直制表符 换页符
        """
        result = value
        # 先转义反斜杠，避免重复转义
        result = result.replace("\\", "\\\\")
        for char, escaped in ESCAPE_MAP.items():
            if char != "\\":
                result = result.replace(char, escaped)
        return result

    @staticmethod
    def encode_value(value: Any) -> str:
        """
        将 Python 值编码为协议字符串

        Args:
            value: Python 值

        Returns:
            编码后的字符串
        """
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            return str(value)
        elif isinstance(value, str):
            return CommandEncoder.escape(value)
        elif isinstance(value, (list, tuple)):
            # 列表类型用于多值参数，用 | 分隔
            return "|".join(CommandEncoder.encode_value(v) for v in value)
        else:
            return CommandEncoder.escape(str(value))

    @staticmethod
    def encode_command(command: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        编码完整命令

        Args:
            command: 命令名称
            params: 命令参数

        Returns:
            编码后的命令字符串

        Example:
            >>> CommandEncoder.encode_command("clientmove", {"clid": 1, "cid": 2})
            'clientmove clid=1 cid=2'
        """
        parts = [command]

        if params:
            for key, value in params.items():
                if value is None:
                    # 无值的参数
                    parts.append(f"-{key}")
                elif isinstance(value, list) and len(value) > 1:
                    # 多值参数：key=value1|value2|value3
                    encoded_values = "|".join(
                        CommandEncoder.encode_value(v) for v in value
                    )
                    parts.append(f"{key}={encoded_values}")
                else:
                    # 单值参数
                    encoded_value = CommandEncoder.encode_value(value)
                    parts.append(f"{key}={encoded_value}")

        return " ".join(parts)

    @staticmethod
    def encode_command_with_options(
        command: str,
        params: Optional[Dict[str, Any]] = None,
        options: Optional[List[str]] = None,
    ) -> str:
        """
        编码带选项的命令

        Args:
            command: 命令名称
            params: 命令参数
            options: 命令选项（如 -uid, -country 等）

        Returns:
            编码后的命令字符串

        Example:
            >>> CommandEncoder.encode_command_with_options(
            ...     "clientlist",
            ...     {},
            ...     ["uid", "country"]
            ... )
            'clientlist -uid -country'
        """
        base = CommandEncoder.encode_command(command, params)

        if options:
            option_str = " ".join(f"-{opt}" for opt in options)
            return f"{base} {option_str}"

        return base
