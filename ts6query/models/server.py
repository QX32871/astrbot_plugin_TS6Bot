"""
服务器信息数据模型
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class VirtualServerInfo:
    """虚拟服务器信息（来自 serverlist 命令）"""

    virtualserver_id: int
    virtualserver_port: int
    virtualserver_status: str
    virtualserver_clientsonline: int
    virtualserver_queryclientsonline: int
    virtualserver_maxclients: int
    virtualserver_uptime: int
    virtualserver_name: str
    virtualserver_autostart: bool = True
    virtualserver_machine_id: str = ""
    virtualserver_unique_identifier: str = ""

    @property
    def is_online(self) -> bool:
        return self.virtualserver_status == "online"

    @property
    def uptime_human(self) -> str:
        """返回人类可读的运行时间"""
        seconds = self.virtualserver_uptime
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}秒")

        return "".join(parts)


@dataclass
class ServerInfo:
    """服务器详细信息（来自 serverinfo 命令）"""

    virtualserver_unique_identifier: str
    virtualserver_name: str
    virtualserver_welcomemessage: str
    virtualserver_platform: str
    virtualserver_version: str
    virtualserver_maxclients: int
    virtualserver_clientsonline: int
    virtualserver_queryclientsonline: int
    virtualserver_channelsonline: int
    virtualserver_created: int
    virtualserver_uptime: int
    virtualserver_port: int
    virtualserver_autostart: bool
    virtualserver_hostmessage: str
    virtualserver_hostmessage_mode: int
    virtualserver_default_server_group: int
    virtualserver_default_channel_group: int
    virtualserver_password: bool
    virtualserver_reserved_slots: int
    virtualserver_icon_id: int
    virtualserver_total_packetloss_speech: float
    virtualserver_total_packetloss_keepalive: float
    virtualserver_total_ping: float

    # 可选字段
    virtualserver_max_download_total_bandwidth: int = 0
    virtualserver_max_upload_total_bandwidth: int = 0
    virtualserver_download_quota: int = 0
    virtualserver_upload_quota: int = 0
    virtualserver_needed_identity_security_level: int = 8

    @property
    def uptime_human(self) -> str:
        """返回人类可读的运行时间"""
        seconds = self.virtualserver_uptime
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}秒")

        return "".join(parts)

    @property
    def created_datetime(self) -> datetime:
        """返回创建时间的 datetime 对象"""
        return datetime.fromtimestamp(self.virtualserver_created)

    @property
    def is_full(self) -> bool:
        """服务器是否已满"""
        return self.virtualserver_clientsonline >= self.virtualserver_maxclients

    @property
    def available_slots(self) -> int:
        """可用槽位"""
        return self.virtualserver_maxclients - self.virtualserver_clientsonline


@dataclass
class HostInfo:
    """主机信息（来自 hostinfo 命令）"""

    instance_uptime: int
    host_timestamp_utc: int
    virtualservers_running_total: int
    virtualservers_total_maxclients: int
    virtualservers_total_clients_online: int
    virtualservers_total_channels_online: int
    connection_filetransfer_bandwidth_sent: int
    connection_filetransfer_bandwidth_received: int
    connection_packets_sent_total: int
    connection_packets_received_total: int
    connection_bytes_sent_total: int
    connection_bytes_received_total: int

    @property
    def uptime_human(self) -> str:
        """返回人类可读的运行时间"""
        seconds = self.instance_uptime
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}秒")

        return "".join(parts)


@dataclass
class VersionInfo:
    """版本信息（来自 version 命令）"""

    version: str
    build: int
    platform: str

    def __str__(self) -> str:
        return f"TeamSpeak {self.version} (build {self.build}) on {self.platform}"
