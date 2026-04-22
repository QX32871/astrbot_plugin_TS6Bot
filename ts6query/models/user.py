"""
用户信息数据模型
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import IntFlag


class ClientType(IntFlag):
    """客户端类型标志"""

    NORMAL = 0
    QUERY = 1
    INTERNAL = 2


class ClientFlag(IntFlag):
    """客户端标志"""

    NONE = 0
    CHANNEL_COMMANDER = 1
    VOIP_MUTED = 2
    NO_MICROPHONE = 4
    AWAY = 8


@dataclass
class ClientListEntry:
    """客户端列表条目（来自 clientlist 命令）"""

    clid: int  # 客户端ID
    cid: int   # 所在频道ID
    client_database_id: int
    client_nickname: str
    client_type: int  # 0=普通用户, 1=ServerQuery客户端
    client_unique_identifier: str = ""
    client_away: bool = False
    client_away_message: str = ""
    client_flag_talking: bool = False
    client_input_muted: bool = False
    client_output_muted: bool = False
    client_input_hardware: bool = True
    client_output_hardware: bool = True
    client_talk_power: int = 0
    client_is_talker: bool = False
    client_is_priority_speaker: bool = False
    client_is_recording: bool = False
    client_is_channel_commander: bool = False
    client_is_query: bool = False
    client_badges: str = ""
    client_platform: str = ""

    @property
    def is_query_client(self) -> bool:
        """是否为 ServerQuery 客户端"""
        return self.client_type == 1

    @property
    def is_voice_client(self) -> bool:
        """是否为语音客户端"""
        return self.client_type == 0

    @property
    def is_away(self) -> bool:
        """是否离开状态"""
        return self.client_away

    @property
    def is_muted(self) -> bool:
        """是否静音"""
        return self.client_input_muted or self.client_output_muted


@dataclass
class UserInfo:
    """用户详细信息（来自 clientinfo 命令）"""

    client_unique_identifier: str
    client_nickname: str
    client_version: str
    client_platform: str
    client_input_muted: bool
    client_output_muted: bool
    client_outputonly_muted: bool
    client_input_hardware: bool
    client_output_hardware: bool
    client_default_channel: str
    client_meta_data: str
    client_is_recording: bool
    client_database_id: int
    client_channel_group_id: int
    client_servergroups: str  # 逗号分隔的服务器组ID列表
    client_created: int
    client_lastconnected: int
    client_totalconnections: int
    client_away: bool
    client_away_message: str
    client_type: int
    client_avatar_hash: str
    client_talk_power: int
    client_talk_power_request: int
    client_description: str
    client_is_talker: bool
    client_month_bytes_uploaded: int
    client_month_bytes_downloaded: int
    client_total_bytes_uploaded: int
    client_total_bytes_downloaded: int
    client_country: str
    client_badges: str
    client_connected_time: int = 0
    client_idle_time: int = 0

    @property
    def server_group_ids(self) -> List[int]:
        """返回服务器组ID列表"""
        if not self.client_servergroups:
            return []
        return [int(g) for g in self.client_servergroups.split(",") if g]

    @property
    def connected_time_human(self) -> str:
        """返回人类可读的连接时间"""
        seconds = self.client_connected_time // 1000  # 毫秒转秒
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}秒")

        return "".join(parts)

    @property
    def idle_time_human(self) -> str:
        """返回人类可读的空闲时间"""
        seconds = self.client_idle_time // 1000  # 毫秒转秒
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}秒")

        return "".join(parts)

    @property
    def is_query_client(self) -> bool:
        """是否为 ServerQuery 客户端"""
        return self.client_type == 1

    @property
    def total_traffic_mb(self) -> float:
        """总流量（MB）"""
        return (self.client_total_bytes_uploaded + self.client_total_bytes_downloaded) / (1024 * 1024)


@dataclass
class BanEntry:
    """封禁条目（来自 banlist 命令）"""

    banid: int
    ip: str = ""
    name: str = ""
    uid: str = ""
    created: int = 0
    duration: int = 0
    invokername: str = ""
    invokercldbid: int = 0
    reason: str = ""
    enforcements: int = 0

    @property
    def is_permanent(self) -> bool:
        """是否为永久封禁"""
        return self.duration == 0

    @property
    def expires_timestamp(self) -> Optional[int]:
        """返回过期时间戳（None 表示永久）"""
        if self.is_permanent:
            return None
        return self.created + self.duration

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.is_permanent:
            return False
        import time
        return time.time() > self.expires_timestamp
