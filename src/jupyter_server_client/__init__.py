import sys
from typing import Literal

import aiohttp

from jupyter_server_client.kernel_websocket import KernelWebSocketClient
from jupyter_server_client.terminal_websocket import TerminalWebSocket

if sys.version_info < (3, 11):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict


class Foo(TypedDict):
    pass


async def _raise_for_status(response: aiohttp.ClientResponse):
    if response.status > 399:
        raise Exception(
            f"请求失败! status_code:{response.status} - request:{response.request_info} - response:{await response.read()}"
        )
    return response


class JupyterServerClient:
    def __init__(
        self, base_url: str = "http://localhost:8888", token: str = ""
    ) -> None:
        self.base_url = base_url.strip("/")

        if self.base_url.startswith("http://"):
            self.ws_base_url = "ws://" + self.base_url[7:]
        elif self.base_url.startswith("https://"):
            self.ws_base_url = "wss://" + self.base_url[8:]
        else:
            raise ValueError(f"无效的 url: {self.base_url}")

        self.token = token

    @property
    def headers(self):
        return {"Authorization": self.token}

    @property
    def session(self):
        if not hasattr(self, "_session"):
            raise NotImplementedError(
                "请通过 async with JupyterServerClient() as client: ... 语法来使用本 Client"
            )
        return self._session

    async def __aenter__(self):
        self._session = await aiohttp.ClientSession(
            base_url=self.base_url,
            headers=self.headers,
        ).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def api(self) -> dict:
        async with self.session.get(
            "/api/",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def get_file_or_dir(self, path: str = "") -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-contents-path"""
        async with self.session.get(
            f"/api/contents/{path}",
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
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#put--api-contents-path"""
        async with self.session.put(
            f"/api/contents/{path}",
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
        return await self._put_contents(
            path=path, content="", format="text", name="", type="directory"
        )

    async def upload_file(
        self, path: str, content: str = "", format: Literal["text", "base64"] = "text"
    ):
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
            f"/api/contents/{path}",
        ) as response:
            await _raise_for_status(response)

    async def create_session(
        self,
        id: str = "",
        kernel: dict | None = None,
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
            "/api/sessions",
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
            "/api/sessions",
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
            f"/api/sessions/{session_id}",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def delete_session(self, session_id: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#delete--api-sessions-session

        Args:
            session (str): _description_
        """
        async with self.session.delete(
            f"/api/sessions/{session_id}",
        ) as response:
            await _raise_for_status(response)

    async def get_kernels(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-kernels

        Returns:
            dict: _description_
        """
        async with self.session.get(
            "/api/kernels",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def start_a_kernel(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-kernels

        Returns:
            dict: _description_
        """
        async with self.session.post(
            "/api/kernels",
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
            f"/api/kernels/{kernel_id}",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def delete_kernel(self, kernel_id: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#delete--api-kernels-kernel_id

        Args:
            kernel (str): _description_
        """
        async with self.session.delete(
            f"/api/kernels/{kernel_id}",
        ) as response:
            await _raise_for_status(response)

    async def interrupt_kernel(self, kernel_id: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-kernels-kernel_id-interrupt

        Args:
            kernel (str): _description_
        """
        async with self.session.post(
            f"/api/kernels/{kernel_id}/interrupt",
        ) as response:
            await _raise_for_status(response)

    async def restart_kernel(self, kernel_id: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-kernels-kernel_id-restart

        Args:
            kernel (str): _description_
        """
        async with self.session.post(
            f"/api/kernels/{kernel_id}/restart",
        ) as response:
            await _raise_for_status(response)

    async def get_kernelspecs(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-kernelspecs

        Returns:
            dict: _description_
        """
        async with self.session.get(
            "/api/kernelspecs",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    def connect_kernel(self, kernel_id: str) -> KernelWebSocketClient:
        return KernelWebSocketClient(
            self.ws_base_url + f"/api/kernels/{kernel_id}/channels",
            headers=self.headers,
        )

    async def get_terminals(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-terminals

        Returns:
            dict: _description_
        """
        async with self.session.get(
            "/api/terminals",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def create_a_terminal(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#post--api-terminals

        Returns:
            dict: _description_
        """
        async with self.session.post(
            "/api/terminals",
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
            f"/api/terminals/{terminal}",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def delete_terminal(self, terminal: str) -> None:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#delete--api-terminals-terminal_id

        Args:
            terminal (str): _description_
        """
        async with self.session.delete(
            f"/api/terminals/{terminal}",
        ) as response:
            await _raise_for_status(response)

    async def api_me(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-me

        Returns:
            dict: _description_
        """
        async with self.session.get(
            "/api/me",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    async def api_status(self) -> dict:
        """https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html#get--api-status

        Returns:
            dict: _description_
        """
        async with self.session.get(
            "/api/status",
        ) as response:
            await _raise_for_status(response)
            return await response.json()

    def connect_terminal(self, terminal: str):
        ws_context = self.session.ws_connect(
            self.ws_base_url + f"/api/terminals/{terminal}/channels",
        )
        return TerminalWebSocket(ws_context)


if __name__ == "__main__":
    import asyncio
    from datetime import datetime

    from rich import print

    client = JupyterServerClient("http://localhost:9999")

    async def test():
        print(await client.api())
        print(await client.get_file_or_dir(""))
        print(await client.get_file_or_dir("24点.png"))

        print(datetime.now(), "mao_file downloading...")
        await client.get_file_or_dir("猫.png")
        print(datetime.now(), "mao_file downloaded")

    asyncio.run(test())
