import sys
from collections.abc import Callable
from typing import Literal

import aiohttp

if sys.version_info < (3, 11):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict


class Foo(TypedDict):
    pass


async def _raise_for_status(response: aiohttp.ClientResponse):
    if response.status > 399:
        raise Exception(f"请求失败! status_code:{response.status} - request:{response.request_info} - response:{await response.read()}")
    return response


class KernelChannelWebSocket:
    def __init__(self, ws_context: aiohttp.client._WSRequestContextManager, msg_process_func: Callable[[aiohttp.WSMessage], None] = lambda msg: print(msg)) -> None:
        self.ws_context = ws_context

        self.msg_process_func = msg_process_func

    @property
    def ws(self):
        if not hasattr(self, "_ws"):
            raise NotImplementedError("请通过 async with KernelChannelWebSocket(ws_context) as ws: ... 语法来使用")
        return self._ws

    async def __aenter__(self):
        self._ws = await self.ws_context.__aenter__()

        asyncio.create_task(self._receive_task())
        asyncio.sleep(0)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.ws_context.__aexit__(exc_type, exc_val, exc_tb)

    async def execute(self, code: str):
        raise NotImplementedError
        data: str = ...
        await self.ws.send_str(data)
        # 从 queue 读取执行结果，直到 idle

    async def _receive_task(self):
        raise NotImplementedError
        async for ws_msg in self.ws:  # noqa: B007
            asyncio.sleep(0)

            # 获取执行结果，保存到 queue
            ...


class TerminalChannelWebSocket:
    def __init__(self, ws_context: aiohttp.client._WSRequestContextManager) -> None:
        self.ws_context = ws_context


class JupyterServerClient:
    def __init__(self, url: str = "http://localhost:8888", token: str = "") -> None:
        self.url = url.strip("/")

        if self.url.startswith("http://"):
            self.ws_url = "ws://" + self.url[7:]
        elif self.url.startswith("https://"):
            self.ws_url = "wss://" + self.url[8:]
        else:
            raise ValueError(f"无效的 url: {self.url}")

        self.token = token

    @property
    def session(self):
        if not hasattr(self, "_session"):
            raise NotImplementedError("请通过 async with JupyterServerClient() as client: ... 语法来使用本 Client")
        return self._session

    async def __aenter__(self):
        self._session = await aiohttp.ClientSession(
            headers={"Authorization": self.token},
        ).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def api(self) -> dict:
        async with self.session.get(
            url=self.url + "/api/",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def get_file_or_dir(self, path: str = "") -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-contents-path"""
        async with self.session.get(
            self.url + f"/api/contents/{path}",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def _put_contents(
        self,
        path: str,
        content: str,
        format: Literal["json", "text", "base64"],
        name: str,
        type: Literal["notebook", "file", "directory"],
    ) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#put--api-contents-path

        1. 文件操作下 name 字段无用
        2. 文件夹
        """
        async with self.session.put(
            self.url + f"/api/contents/{path}",
            json=dict(
                content=content,
                format=format,
                name=name,
                path=path,
                type=type,
            ),
        ) as response:
            print(f"{path=} - {response.status=} - {response.reason=}")
            await _raise_for_status(response)
            return await response.json()

    async def create_dir(self, path: str):
        """创建文件夹，path 是相对路径，如果是绝对路径会 404，如果已经存在不会有任何提示也不会有操作。

        Args:
            path (str, optional): _description_. Defaults to "".

        Returns:
            _type_: _description_
        """
        return await self._put_contents(path=path, content="", format="text", name="", type="directory")

    async def upload_file(self, path: str, content: str = "", format: Literal["text", "base64"] = "text"):
        """上传文件，path 是相对路径，如果是绝对路径会 404
        如果文件目录不存在会 500

        Args:
            path (str): _description_
            content (str, optional): _description_. Defaults to "".
            format (Literal[&quot;text&quot;, &quot;base64&quot;], optional): _description_. Defaults to "text".

        Returns:
            _type_: _description_
        """
        return await self._put_contents(
            path=path,
            content=content,
            format=format,
            name="",
            type="file",
        )

    async def delete_file(self, path: str = "") -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#delete--api-contents-path

        不存在会 404"""
        async with self.session.delete(
            self.url + f"/api/contents/{path}",
        ) as response:
            await _raise_for_status(response)

    async def create_session(
        self,
        id: str = "",
        kernel: dict = None,
        name: str = "",
        path: str = "",
        type: str = "",
    ) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-sessions

        Returns:
            dict: _description_
        """
        if kernel is None:
            kernel = {"name": "python3"}
        async with self.session.post(
            self.url + "/api/sessions",
            json=dict(
                id=id,
                kernel=kernel,
                name=name,
                path=path,
                type=type,
            ),
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def get_sessions(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-sessions

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + "/api/sessions",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def get_session(self, session_id: str) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-sessions-session
        不存在会 404

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + f"/api/sessions/{session_id}",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def delete_session(self, session_id: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#delete--api-sessions-session

        Args:
            session (str): _description_
        """
        async with self.session.delete(
            self.url + f"/api/sessions/{session_id}",
        ) as response:
            await _raise_for_status(response)

    async def get_kernels(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-kernels

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + "/api/kernels",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def start_a_kernel(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-kernels

        Returns:
            dict: _description_
        """
        async with self.session.post(
            self.url + "/api/kernels",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def get_kernel(self, kernel_id: str) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-kernels-kernel_id

        Args:
            kernel (str): _description_

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + f"/api/kernels/{kernel_id}",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def delete_kernel(self, kernel_id: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#delete--api-kernels-kernel_id

        Args:
            kernel (str): _description_
        """
        async with self.session.delete(
            self.url + f"/api/kernels/{kernel_id}",
        ) as response:
            await _raise_for_status(response)

    async def interrupt_kernel(self, kernel_id: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-kernels-kernel_id-interrupt

        Args:
            kernel (str): _description_
        """
        async with self.session.post(
            self.url + f"/api/kernels/{kernel_id}/interrupt",
        ) as response:
            await _raise_for_status(response)

    async def restart_kernel(self, kernel_id: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-kernels-kernel_id-restart

        Args:
            kernel (str): _description_
        """
        async with self.session.post(
            self.url + f"/api/kernels/{kernel_id}/restart",
        ) as response:
            await _raise_for_status(response)

    async def get_kernelspecs(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-kernelspecs

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + "/api/kernelspecs",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    def connect_kernel(self, kernel_id: str) -> None:
        ws_context = self.session.ws_connect(
            self.ws_url + f"/api/kernels/{kernel_id}/channels",
        )
        return KernelChannelWebSocket(ws_context)

    async def get_terminals(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-terminals

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + "/api/terminals",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def create_a_terminal(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-terminals

        Returns:
            dict: _description_
        """
        async with self.session.post(
            self.url + "/api/terminals",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def get_terminal(self, terminal: str) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-terminals-terminal_id

        Args:
            terminal (str): _description_

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + f"/api/terminals/{terminal}",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def delete_terminal(self, terminal: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#delete--api-terminals-terminal_id

        Args:
            terminal (str): _description_
        """
        async with self.session.delete(
            self.url + f"/api/terminals/{terminal}",
        ) as response:
            await _raise_for_status(response)

    async def api_me(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-me

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + "/api/me",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def api_status(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-status

        Returns:
            dict: _description_
        """
        async with self.session.get(
            self.url + "/api/status",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    def connect_terminal(self, terminal: str) -> None:
        ws_context = self.session.ws_connect(
            self.ws_url + f"/api/terminals/{terminal}/channels",
        )
        return TerminalChannelWebSocket(ws_context)


if __name__ == "__main__":
    import asyncio
    from datetime import datetime

    from rich import print

    client = JupyterServerClient("http://localhost:9999")

    async def test():
        print(await client.api())
        print(await client.contents(""))
        print(await client.contents("24点.png"))

        print(datetime.now(), "mao_file downloading...")
        await client.contents("猫.png")
        print(datetime.now(), "mao_file downloaded")

    asyncio.run(test())
