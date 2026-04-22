"""
数据模型单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ts6query.models.server import ServerInfo, VirtualServerInfo, VersionInfo
from ts6query.models.user import UserInfo, ClientListEntry, BanEntry


class TestVirtualServerInfo:
    """VirtualServerInfo 测试"""

    def test_is_online_true(self):
        """测试在线状态为 True"""
        info = VirtualServerInfo(
            virtualserver_id=1,
            virtualserver_port=9987,
            virtualserver_status="online",
            virtualserver_clientsonline=5,
            virtualserver_queryclientsonline=1,
            virtualserver_maxclients=32,
            virtualserver_uptime=12345,
            virtualserver_name="Test Server"
        )
        assert info.is_online is True

    def test_is_online_false(self):
        """测试在线状态为 False"""
        info = VirtualServerInfo(
            virtualserver_id=1,
            virtualserver_port=9987,
            virtualserver_status="offline",
            virtualserver_clientsonline=0,
            virtualserver_queryclientsonline=0,
            virtualserver_maxclients=32,
            virtualserver_uptime=0,
            virtualserver_name="Test Server"
        )
        assert info.is_online is False

    def test_uptime_human_format(self):
        """测试运行时间格式化"""
        # 1天2小时3分钟4秒 = 86400 + 7200 + 180 + 4 = 93784
        info = VirtualServerInfo(
            virtualserver_id=1,
            virtualserver_port=9987,
            virtualserver_status="online",
            virtualserver_clientsonline=5,
            virtualserver_queryclientsonline=1,
            virtualserver_maxclients=32,
            virtualserver_uptime=93784,
            virtualserver_name="Test Server"
        )
        assert info.uptime_human == "1天2小时3分钟4秒"

    def test_uptime_human_only_seconds(self):
        """测试仅秒的运行时间格式化"""
        info = VirtualServerInfo(
            virtualserver_id=1,
            virtualserver_port=9987,
            virtualserver_status="online",
            virtualserver_clientsonline=5,
            virtualserver_queryclientsonline=1,
            virtualserver_maxclients=32,
            virtualserver_uptime=30,
            virtualserver_name="Test Server"
        )
        assert info.uptime_human == "30秒"


class TestServerInfo:
    """ServerInfo 测试"""

    @pytest.fixture
    def sample_server_info(self):
        """创建示例服务器信息"""
        return ServerInfo(
            virtualserver_unique_identifier="abc123",
            virtualserver_name="Test Server",
            virtualserver_welcomemessage="Welcome!",
            virtualserver_platform="Windows",
            virtualserver_version="3.13.0",
            virtualserver_maxclients=32,
            virtualserver_clientsonline=10,
            virtualserver_queryclientsonline=2,
            virtualserver_channelsonline=15,
            virtualserver_created=1609459200,  # 2021-01-01
            virtualserver_uptime=86400,
            virtualserver_port=9987,
            virtualserver_autostart=True,
            virtualserver_hostmessage="Hello",
            virtualserver_hostmessage_mode=1,
            virtualserver_default_server_group=1,
            virtualserver_default_channel_group=1,
            virtualserver_password=False,
            virtualserver_reserved_slots=5,
            virtualserver_icon_id=0,
            virtualserver_total_packetloss_speech=0.0,
            virtualserver_total_packetloss_keepalive=0.0,
            virtualserver_total_ping=15.5
        )

    def test_is_full_false(self, sample_server_info):
        """测试服务器未满"""
        assert sample_server_info.is_full is False

    def test_is_full_true(self, sample_server_info):
        """测试服务器已满"""
        sample_server_info.virtualserver_clientsonline = 32
        assert sample_server_info.is_full is True

    def test_available_slots(self, sample_server_info):
        """测试可用槽位"""
        assert sample_server_info.available_slots == 22

    def test_uptime_human(self, sample_server_info):
        """测试运行时间格式化"""
        assert sample_server_info.uptime_human == "1天"


class TestVersionInfo:
    """VersionInfo 测试"""

    def test_str_representation(self):
        """测试字符串表示"""
        info = VersionInfo(
            version="3.13.0",
            build=12345,
            platform="Windows"
        )
        assert str(info) == "TeamSpeak 3.13.0 (build 12345) on Windows"


class TestClientListEntry:
    """ClientListEntry 测试"""

    def test_is_query_client_true(self):
        """测试 ServerQuery 客户端判断"""
        entry = ClientListEntry(
            clid=1,
            cid=2,
            client_database_id=100,
            client_nickname="QueryBot",
            client_type=1
        )
        assert entry.is_query_client is True
        assert entry.is_voice_client is False

    def test_is_voice_client_true(self):
        """测试语音客户端判断"""
        entry = ClientListEntry(
            clid=1,
            cid=2,
            client_database_id=100,
            client_nickname="User",
            client_type=0
        )
        assert entry.is_voice_client is True
        assert entry.is_query_client is False

    def test_is_away_true(self):
        """测试离开状态判断"""
        entry = ClientListEntry(
            clid=1,
            cid=2,
            client_database_id=100,
            client_nickname="User",
            client_type=0,
            client_away=True
        )
        assert entry.is_away is True

    def test_is_muted_true(self):
        """测试静音状态判断"""
        entry = ClientListEntry(
            clid=1,
            cid=2,
            client_database_id=100,
            client_nickname="User",
            client_type=0,
            client_input_muted=True
        )
        assert entry.is_muted is True


class TestUserInfo:
    """UserInfo 测试"""

    @pytest.fixture
    def sample_user_info(self):
        """创建示例用户信息"""
        return UserInfo(
            client_unique_identifier="abc123",
            client_nickname="TestUser",
            client_version="3.13.0",
            client_platform="Windows",
            client_input_muted=False,
            client_output_muted=False,
            client_outputonly_muted=False,
            client_input_hardware=True,
            client_output_hardware=True,
            client_default_channel="1",
            client_meta_data="",
            client_is_recording=False,
            client_database_id=100,
            client_channel_group_id=1,
            client_servergroups="2,3,5",
            client_created=1609459200,
            client_lastconnected=1640995200,
            client_totalconnections=50,
            client_away=False,
            client_away_message="",
            client_type=0,
            client_avatar_hash="",
            client_talk_power=75,
            client_talk_power_request=0,
            client_description="",
            client_is_talker=False,
            client_month_bytes_uploaded=1048576,
            client_month_bytes_downloaded=2097152,
            client_total_bytes_uploaded=10485760,
            client_total_bytes_downloaded=20971520,
            client_country="CN",
            client_badges="",
            client_connected_time=3600000,  # 1小时（毫秒）
            client_idle_time=300000  # 5分钟（毫秒）
        )

    def test_server_group_ids(self, sample_user_info):
        """测试服务器组 ID 列表"""
        assert sample_user_info.server_group_ids == [2, 3, 5]

    def test_server_group_ids_empty(self):
        """测试空服务器组 ID 列表"""
        info = UserInfo(
            client_unique_identifier="abc123",
            client_nickname="TestUser",
            client_version="3.13.0",
            client_platform="Windows",
            client_input_muted=False,
            client_output_muted=False,
            client_outputonly_muted=False,
            client_input_hardware=True,
            client_output_hardware=True,
            client_default_channel="1",
            client_meta_data="",
            client_is_recording=False,
            client_database_id=100,
            client_channel_group_id=1,
            client_servergroups="",  # 空
            client_created=1609459200,
            client_lastconnected=1640995200,
            client_totalconnections=50,
            client_away=False,
            client_away_message="",
            client_type=0,
            client_avatar_hash="",
            client_talk_power=75,
            client_talk_power_request=0,
            client_description="",
            client_is_talker=False,
            client_month_bytes_uploaded=0,
            client_month_bytes_downloaded=0,
            client_total_bytes_uploaded=0,
            client_total_bytes_downloaded=0,
            client_country="CN",
            client_badges=""
        )
        assert info.server_group_ids == []

    def test_connected_time_human(self, sample_user_info):
        """测试连接时间格式化"""
        assert sample_user_info.connected_time_human == "1小时"

    def test_idle_time_human(self, sample_user_info):
        """测试空闲时间格式化"""
        assert sample_user_info.idle_time_human == "5分钟"

    def test_total_traffic_mb(self, sample_user_info):
        """测试总流量计算"""
        # 10485760 + 20971520 = 31457280 bytes = 30 MB
        assert abs(sample_user_info.total_traffic_mb - 30.0) < 0.01


class TestBanEntry:
    """BanEntry 测试"""

    def test_is_permanent_true(self):
        """测试永久封禁判断"""
        ban = BanEntry(banid=1, duration=0)
        assert ban.is_permanent is True

    def test_is_permanent_false(self):
        """测试临时封禁判断"""
        ban = BanEntry(banid=1, duration=3600)
        assert ban.is_permanent is False

    def test_is_expired_permanent(self):
        """测试永久封禁永不过期"""
        ban = BanEntry(banid=1, duration=0)
        assert ban.is_expired is False

    def test_expires_timestamp_permanent(self):
        """测试永久封禁过期时间"""
        ban = BanEntry(banid=1, duration=0)
        assert ban.expires_timestamp is None

    def test_expires_timestamp_temporary(self):
        """测试临时封禁过期时间"""
        ban = BanEntry(
            banid=1,
            created=1000000,
            duration=3600
        )
        assert ban.expires_timestamp == 1003600
