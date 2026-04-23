"""
TS6 ServerQuery AstrBot 插件

提供 TeamSpeak 6 服务器信息查询和用户管理功能。
"""

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from ts6query import TS6QueryClient, ConnectionType
from ts6query.exceptions import TS6QueryError


@register("astrbot_plugin_ts6_info_fetcher", "QX32871", "TS6服务器信息查询插件", "1.0.0")
class TS6BotPlugin(Star):
    """TeamSpeak 6 服务器信息查询插件"""

    def __init__(self, context: Context):
        super().__init__(context)
        self._client: TS6QueryClient | None = None
        self._config = self._get_config()

    def _get_config(self) -> dict:
        """获取插件配置"""
        # AstrBot 会自动管理插件配置
        # 配置项在配置文件中定义
        config = getattr(self.context, 'config', {}) or {}
        return {
            "host": config.get("ts6_host", "localhost"),
            "port": config.get("ts6_port", 10011),
            "username": config.get("ts6_username", "serveradmin"),
            "password": config.get("ts6_password", ""),
            "connection_type": config.get("ts6_connection_type", "tcp"),
            "server_id": config.get("ts6_server_id", 1),
        }

    async def initialize(self):
        """插件初始化"""
        logger.info("TS6Bot 插件初始化中...")
        self._client = TS6QueryClient()

    async def terminate(self):
        """插件销毁"""
        logger.info("TS6Bot 插件销毁中...")
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        self._client = None

    async def _ensure_connected(self) -> bool:
        """确保已连接到服务器"""
        if not self._client:
            return False

        if self._client.is_connected:
            return True

        try:
            conn_type = (
                ConnectionType.SSH
                if self._config.get("connection_type") == "ssh"
                else ConnectionType.TCP
            )

            await self._client.connect(
                host=self._config["host"],
                port=self._config["port"],
                username=self._config["username"],
                password=self._config["password"],
                connection_type=conn_type,
            )

            # 选择虚拟服务器
            if self._config.get("server_id"):
                await self._client.use_server(self._config["server_id"])

            return True

        except TS6QueryError as e:
            logger.error(f"连接 TS6 服务器失败: {e}")
            return False

    @filter.command("ts6_status")
    async def ts6_status(self, event: AstrMessageEvent):
        """查询 TS6 服务器状态"""
        if not await self._ensure_connected():
            yield event.plain_result("❌ 无法连接到 TS6 服务器")
            return

        try:
            info = await self._client.server_info()
            version = await self._client.version()

            status_msg = (
                f"📊 **TeamSpeak 6 服务器状态**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🖥️ 服务器名称: {info.get('virtualserver_name', 'N/A')}\n"
                f"📋 版本: {version.get('version', 'N/A')}\n"
                f"👥 在线用户: {info.get('virtualserver_clientsonline', 0)}/{info.get('virtualserver_maxclients', 0)}\n"
                f"📺 频道数: {info.get('virtualserver_channelsonline', 0)}\n"
                f"⏱️ 运行时间: {self._format_uptime(info.get('virtualserver_uptime', 0))}\n"
            )

            yield event.plain_result(status_msg)

        except TS6QueryError as e:
            logger.error(f"查询服务器状态失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {e}")

    @filter.command("ts6_clients")
    async def ts6_clients(self, event: AstrMessageEvent):
        """查询 TS6 在线用户列表"""
        if not await self._ensure_connected():
            yield event.plain_result("❌ 无法连接到 TS6 服务器")
            return

        try:
            clients = await self._client.client_list(uid=True)

            if not clients:
                yield event.plain_result("📭 当前没有在线用户")
                return

            # 过滤掉 ServerQuery 客户端
            voice_clients = [c for c in clients if c.get("client_type", 0) == 0]

            if not voice_clients:
                yield event.plain_result("📭 当前没有语音用户在线")
                return

            lines = ["👥 **在线用户列表**", "━━━━━━━━━━━━━━━━━━"]
            for i, client in enumerate(voice_clients[:20], 1):  # 限制显示 20 个
                nickname = client.get("client_nickname", "未知")
                away = "💤" if client.get("client_away", False) else ""
                muted = "🔇" if client.get("client_output_muted", False) else ""
                lines.append(f"{i}. {nickname} {away}{muted}")

            if len(voice_clients) > 20:
                lines.append(f"... 还有 {len(voice_clients) - 20} 位用户")

            yield event.plain_result("\n".join(lines))

        except TS6QueryError as e:
            logger.error(f"查询用户列表失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {e}")

    @filter.command("ts6_kick")
    async def ts6_kick(self, event: AstrMessageEvent):
        """踢出 TS6 用户 (用法: /ts6_kick <用户名> [原因])"""
        args = event.message_str.split(maxsplit=2)

        if len(args) < 2:
            yield event.plain_result("用法: /ts6_kick <用户名> [原因]")
            return

        nickname = args[1]
        reason = args[2] if len(args) > 2 else ""

        if not await self._ensure_connected():
            yield event.plain_result("❌ 无法连接到 TS6 服务器")
            return

        try:
            # 查找用户
            clients = await self._client.client_list()
            target = None

            for client in clients:
                if client.get("client_nickname", "").lower() == nickname.lower():
                    target = client
                    break

            if not target:
                yield event.plain_result(f"❌ 未找到用户: {nickname}")
                return

            # 踢出用户
            await self._client.client_kick(
                target["clid"],
                reason_id=5,  # 踢出服务器
                reason_msg=reason or "被管理员踢出"
            )

            yield event.plain_result(f"✅ 已踢出用户: {nickname}")

        except TS6QueryError as e:
            logger.error(f"踢出用户失败: {e}")
            yield event.plain_result(f"❌ 踢出失败: {e}")

    @filter.command("ts6_move")
    async def ts6_move(self, event: AstrMessageEvent):
        """移动 TS6 用户到指定频道 (用法: /ts6_move <用户名> <频道ID>)"""
        args = event.message_str.split(maxsplit=2)

        if len(args) < 3:
            yield event.plain_result("用法: /ts6_move <用户名> <频道ID>")
            return

        nickname = args[1]
        try:
            channel_id = int(args[2])
        except ValueError:
            yield event.plain_result("❌ 频道 ID 必须是数字")
            return

        if not await self._ensure_connected():
            yield event.plain_result("❌ 无法连接到 TS6 服务器")
            return

        try:
            # 查找用户
            clients = await self._client.client_list()
            target = None

            for client in clients:
                if client.get("client_nickname", "").lower() == nickname.lower():
                    target = client
                    break

            if not target:
                yield event.plain_result(f"❌ 未找到用户: {nickname}")
                return

            # 移动用户
            await self._client.client_move(target["clid"], channel_id)

            yield event.plain_result(f"✅ 已将 {nickname} 移动到频道 {channel_id}")

        except TS6QueryError as e:
            logger.error(f"移动用户失败: {e}")
            yield event.plain_result(f"❌ 移动失败: {e}")

    @filter.command("ts6_banlist")
    async def ts6_banlist(self, event: AstrMessageEvent):
        """查询 TS6 封禁列表"""
        if not await self._ensure_connected():
            yield event.plain_result("❌ 无法连接到 TS6 服务器")
            return

        try:
            bans = await self._client.ban_list()

            if not bans:
                yield event.plain_result("📭 当前没有封禁记录")
                return

            lines = ["🚫 **封禁列表**", "━━━━━━━━━━━━━━━━━━"]
            for ban in bans[:10]:  # 限制显示 10 条
                ban_id = ban.get("banid", 0)
                name = ban.get("name", "*")
                ip = ban.get("ip", "*")
                reason = ban.get("reason", "无原因")
                duration = ban.get("duration", 0)
                duration_str = "永久" if duration == 0 else f"{duration}秒"

                lines.append(f"#{ban_id}: {name or ip} - {reason} ({duration_str})")

            if len(bans) > 10:
                lines.append(f"... 还有 {len(bans) - 10} 条封禁记录")

            yield event.plain_result("\n".join(lines))

        except TS6QueryError as e:
            logger.error(f"查询封禁列表失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {e}")

    @filter.command("ts6_help")
    async def ts6_help(self, event: AstrMessageEvent):
        """显示 TS6 插件帮助信息"""
        help_msg = (
            "📖 **TS6 插件命令帮助**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "/ts6_status - 查询服务器状态\n"
            "/ts6_clients - 查询在线用户\n"
            "/ts6_kick <用户名> [原因] - 踢出用户\n"
            "/ts6_move <用户名> <频道ID> - 移动用户\n"
            "/ts6_banlist - 查询封禁列表\n"
            "/ts6_help - 显示此帮助"
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
        if seconds > 0 or not parts:
            parts.append(f"{seconds}秒")

        return "".join(parts)
