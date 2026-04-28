"""
TS6 HTTP API 异步客户端

封装 TeamSpeak 6 HTTP API 的异步请求，提供服务器信息查询功能。
"""

import aiohttp


class TS6HttpClient:
    """TS6 HTTP API 异步客户端"""

    def __init__(self, api_base_url: str, api_key: str):
        self._base_url = api_base_url.rstrip("/")
        self._api_key = api_key
        self._session: aiohttp.ClientSession | None = None
        self._timeout = aiohttp.ClientTimeout(total=10)

    async def start(self):
        self._session = aiohttp.ClientSession(
            headers={
                "x-api-key": self._api_key,
                "Content-Type": "application/json",
            },
            timeout=self._timeout,
        )

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def _get(self, command: str) -> list[dict]:
        """发送 GET 请求到 TS6 HTTP API，返回 body 数组"""
        if not self._session:
            raise RuntimeError("客户端未初始化")
        url = f"{self._base_url}/1/{command}"
        try:
            async with self._session.get(url) as resp:
                data = await resp.json()
                if data["status"]["code"] != 0:
                    raise RuntimeError(
                        f"API 返回错误: {data['status']['message']}"
                    )
                return data.get("body", [])
        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络请求失败: {e}") from e

    async def version(self) -> dict:
        """获取服务器版本"""
        body = await self._get("version")
        return body[0] if body else {}

    async def server_info(self) -> dict:
        """获取服务器信息"""
        body = await self._get("serverinfo")
        return body[0] if body else {}

    async def client_list(self) -> list[dict]:
        """获取在线用户列表"""
        return await self._get("clientlist")

    async def channel_list(self) -> list[dict]:
        """获取频道列表"""
        return await self._get("channellist")

    async def whoami(self) -> dict:
        """获取当前查询会话信息"""
        body = await self._get("whoami")
        return body[0] if body else {}
