"""
TS6 ServerQuery AstrBot 插件

基于 TS6 HTTP API 提供 TeamSpeak 服务器信息查询功能。
"""

from ts6_client import TS6HttpClient

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.core import AstrBotConfig


class TS6BotPlugin(Star):
    """TeamSpeak 6 服务器信息查询插件"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self._client: TS6HttpClient | None = None
        self._config = config

    async def initialize(self):
        """插件初始化"""
        logger.info("TS6Bot 插件初始化中...")
        server_url = self._config.get("server_url", "")
        server_port = self._config.get("server_port", "10080")
        api_key = self._config.get("api_key", "")
        if not server_url or not api_key:
            logger.warning("未配置 server_url 或 api_key，跳过客户端初始化")
            return
        base_url = f"http://{server_url}:{server_port}"
        self._client = TS6HttpClient(base_url, api_key)
        await self._client.start()
        logger.info("TS6 HTTP 客户端已就绪")

    async def terminate(self):
        """插件销毁"""
        logger.info("TS6Bot 插件销毁中...")
        if self._client:
            await self._client.close()
            self._client = None

    async def _ensure_client(self) -> TS6HttpClient | None:
        """确保客户端已初始化，返回客户端或 None"""
        if self._client:
            return self._client
        logger.warning("客户端未初始化，尝试使用当前配置初始化")
        server_url = self._config.get("server_url", "")
        server_port = self._config.get("server_port", "10080")
        api_key = self._config.get("api_key", "")
        if not server_url or not api_key:
            return None
        base_url = f"http://{server_url}:{server_port}"
        self._client = TS6HttpClient(base_url, api_key)
        await self._client.start()
        return self._client

    @filter.command("ts6_status", alias={"状态", "server"})
    async def ts6_status(self, event: AstrMessageEvent):
        """查询 TS 服务器状态"""
        client = await self._ensure_client()
        if not client:
            yield event.plain_result("未配置 API 连接信息")
            return
        try:
            info = await client.server_info()
            status_msg = (
                f"📊 **服务器状态**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🖥️ 服务器名称: {info.get('virtualserver_name', 'N/A')}\n"
                f"📌 版本: {info.get('virtualserver_version', 'N/A')}\n"
                f"👥 在线用户: {info.get('virtualserver_clientsonline', 0)}/"
                f"{info.get('virtualserver_maxclients', 0)}\n"
                f"📢 频道数: {info.get('virtualserver_channelsonline', 0)}\n"
                f"⏱️ 运行时间: {self._format_uptime(int(info.get('virtualserver_uptime', 0)))}\n"
            )
            yield event.plain_result(status_msg)
        except RuntimeError as e:
            logger.error(f"查询服务器状态失败: {e}")
            yield event.plain_result(f"查询失败: {e}")

    @filter.command("ts6_clients", alias={"人呢"})
    async def ts6_clients(self, event: AstrMessageEvent):
        """查询 TS 在线用户列表"""
        client = await self._ensure_client()
        if not client:
            yield event.plain_result("未配置 API 连接信息")
            return
        try:
            clients = await client.client_list()
            if not clients:
                yield event.plain_result("当前没有在线用户")
                return
            voice_clients = [c for c in clients if c.get("client_type", "0") == "0"]
            if not voice_clients:
                yield event.plain_result("当前没有普通用户在线")
                return
            lines = ["👥 **在线用户列表**", "━━━━━━━━━━━━━━━━━━"]
            for i, c in enumerate(voice_clients[:20], 1):
                nickname = c.get("client_nickname", "未知")
                lines.append(f"{i}. {nickname}")
            if len(voice_clients) > 20:
                lines.append(f"... 还有 {len(voice_clients) - 20} 位用户")
            yield event.plain_result("\n".join(lines))
        except RuntimeError as e:
            logger.error(f"查询用户列表失败: {e}")
            yield event.plain_result(f"查询失败: {e}")

    @filter.command("ts6_channels")
    async def ts6_channels(self, event: AstrMessageEvent):
        """查询 TS 频道列表"""
        client = await self._ensure_client()
        if not client:
            yield event.plain_result("未配置 API 连接信息")
            return
        try:
            channels = await client.channel_list()
            if not channels:
                yield event.plain_result("当前没有频道")
                return
            lines = ["📢 **频道列表**", "━━━━━━━━━━━━━━━━━━"]
            for ch in channels[:20]:
                name = ch.get("channel_name", "未知")
                cid = ch.get("cid", "?")
                total = ch.get("total_clients", "0")
                lines.append(f"#{cid} {name} ({total} 人)")
            if len(channels) > 20:
                lines.append(f"... 还有 {len(channels) - 20} 个频道")
            yield event.plain_result("\n".join(lines))
        except RuntimeError as e:
            logger.error(f"查询频道列表失败: {e}")
            yield event.plain_result(f"查询失败: {e}")

    @filter.command("ts6_version")
    async def ts6_version(self, event: AstrMessageEvent):
        """查询 TS 服务器版本"""
        client = await self._ensure_client()
        if not client:
            yield event.plain_result("未配置 API 连接信息")
            return
        try:
            ver = await client.version()
            version_msg = (
                f"🔖 **服务器版本**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"版本: {ver.get('version', 'N/A')}\n"
                f"构建: {ver.get('build', 'N/A')}\n"
                f"平台: {ver.get('platform', 'N/A')}\n"
            )
            yield event.plain_result(version_msg)
        except RuntimeError as e:
            logger.error(f"查询版本失败: {e}")
            yield event.plain_result(f"查询失败: {e}")

    @filter.command("ts6_whoami")
    async def ts6_whoami(self, event: AstrMessageEvent):
        """查询当前 API Key 对应的会话信息"""
        client = await self._ensure_client()
        if not client:
            yield event.plain_result("未配置 API 连接信息")
            return
        try:
            info = await client.whoami()
            msg = (
                f"🔑 **查询会话信息**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"查询昵称: {info.get('client_nickname', 'N/A')}\n"
                f"登录名: {info.get('client_login_name', 'N/A')}\n"
                f"数据库 ID: {info.get('client_database_id', 'N/A')}\n"
                f"所在频道: {info.get('client_channel_id', 'N/A')}\n"
                f"虚拟服务器: {info.get('virtualserver_id', 'N/A')}\n"
                f"服务器状态: {info.get('virtualserver_status', 'N/A')}\n"
            )
            yield event.plain_result(msg)
        except RuntimeError as e:
            logger.error(f"查询会话信息失败: {e}")
            yield event.plain_result(f"查询失败: {e}")

    @filter.command("ts_help", alias={"help"})
    async def ts_help(self, event: AstrMessageEvent):
        """显示插件帮助信息"""
        help_msg = (
            "📖 **TS6 插件命令帮助**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "/ts6_status — 查询服务器状态\n"
            "/ts6_clients — 查询在线用户\n"
            "/ts6_channels — 查询频道列表\n"
            "/ts6_version — 查询服务器版本\n"
            "/ts6_whoami — 查询会话信息\n"
            "/ts_help — 显示此帮助"
        )
        yield event.plain_result(help_msg)

    @staticmethod
    def _format_uptime(seconds: int) -> str:
        """格式化运行时间"""
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
        if not parts:
            parts.append(f"{seconds}秒")
        return "".join(parts)
