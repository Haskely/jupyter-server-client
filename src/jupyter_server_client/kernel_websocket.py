# https://jupyter-client.readthedocs.io/en/latest/messaging.html#general-message-format
import aiohttp
import asyncio
from rich import print
from uuid import uuid4
from typing import Literal, TypedDict


class StreamOutput(TypedDict):
    output_type: Literal["stream"]
    name: Literal["stdout"]
    text: str


class ErrorOutput(TypedDict):
    output_type: Literal["error"]
    ename: str
    evalue: str
    traceback: list[str]


class DataOutput(TypedDict):
    output_type: Literal["display_data"]
    metadata: dict
    data: dict[Literal["text/plain", "image/png"], str]


class ExecOutput(TypedDict):
    output_type: Literal["execute_result"]
    metadata: dict
    data: dict[Literal["text/plain"], str]
    execution_count: int


class KernelWebSocketClient:
    def __init__(self, ws_url: str, headers: dict = {}) -> None:
        self.ws_url = ws_url
        self.headers = headers

    @property
    def ws(self):
        if not hasattr(self, "_ws"):
            raise NotImplementedError(
                "请通过 async with KernelChannelWebSocket(ws_context) as ws: ... 语法来使用"
            )
        return self._ws

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        await self.session.__aenter__()
        self.ws_context = self.session.ws_connect(self.ws_url)
        self._ws = await self.ws_context.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.ws_context.__aexit__(exc_type, exc_val, exc_tb)
        await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def execute(self, code: str, timeout: int = 10):
        """References:
        - https://github.com/jupyter/kernel_gateway_demos/blob/master/python_client_example/src/client.py#L63
        - https://jupyter-client.readthedocs.io/en/latest/messaging.html#general-message-format
        """
        data = {
            "header": {
                # process name for example
                "username": "",
                # The session id in a message header identifies a unique entity with state, such as a kernel process or client process.
                # If a client disconnects and reconnects to a kernel,
                # and messages from the kernel have a different kernel session id than prior to the disconnect,
                # the client should assume that the kernel was restarted.
                "session": "",
                # typically UUID, must be unique per message
                "msg_id": uuid4().hex,
                "msg_type": "execute_request",
                # the message protocol version
                "version": "5.0",
                # ISO 8601 timestamp for when the message is created
                "date": "",
            },
            # When a message is the “result” of another message, such as a side-effect (output or status) or direct reply,
            # the parent_header is a copy of the header of the message that “caused” the current message.
            "parent_header": {},
            "channel": "shell",
            "content": {
                "code": code,
                "silent": False,
                "store_history": True,
                "user_expressions": None,
                "allow_stdin": True,
                "stop_on_error": True,
            },
            "metadata": {},
            "buffers": {},
        }
        print(data)
        await self.ws.send_json(data)

        # 从 queue 读取执行结果，直到 idle
        async def _receive_task():
            while True:
                msg: dict[str, dict] = await self.ws.receive_json()
                print(msg)
                if (
                    msg["parent_header"]["msg_id"] == data["header"]["msg_id"]  # type: ignore
                    and msg["header"]["msg_type"] == "status"
                    and msg["content"]["execution_state"] == "idle"
                ):
                    break

        try:
            await asyncio.wait_for(_receive_task(), timeout=timeout)
        except asyncio.TimeoutError:
            print("timeout")


if __name__ == "__main__":
    pass
