import aiohttp


class TerminalWebSocket:
    def __init__(self, ws_context: aiohttp.client._WSRequestContextManager) -> None:
        self.ws_context = ws_context