import pexpect
from typing import Literal
import asyncio

"""
# https://jupyter-server.readthedocs.io/en/latest/users/configuration.html
jupyter server \
    --IdentityProvider.token="" \
    --ServerApp.allow_credentials=True \
    --ServerApp.allow_external_kernels=True \
    --ServerApp.allow_origin="*" \
    --ServerApp.allow_remote_access=True \
    --ServerApp.disable_check_xsrf=True \
    --ServerApp.ip="0.0.0.0" \
    --ServerApp.open_browser=False \
    --ServerApp.port=8888 \
    --ServerApp.root_dir="/home/jovyan/jupyter_workdir"
"""

class JupyterServerRunner:
    def __init__(
        self, 
        app: Literal["server", "notebook", "lab"] = "server",
        port: int | None = None,
        work_dir: str | None = None,
        token: str | None = None,
    ):
        self.server_process = None
        self.args = [
            app,
            "--ServerApp.allow_credentials", "True",
            "--ServerApp.allow_external_kernels", "True",
            "--ServerApp.allow_origin", "*",
            "--ServerApp.allow_remote_access", "True",
            "--ServerApp.disable_check_xsrf", "True",
            "--ServerApp.ip", "0.0.0.0",
            "--ServerApp.open_browser", "False",
        ]
        if port is not None:
            self.args.append("--ServerApp.port")
            self.args.append(str(port))
        if work_dir is not None:
            self.args.append("--ServerApp.root_dir")
            self.args.append(work_dir)
        if token is not None:
            self.args.append("--IdentityProvider.token")
            self.args.append(token)
            
    def __enter__(self):
        self.start_server()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_server()
        
    async def __aenter__(self):
        await asyncio.to_thread(self.start_server)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.to_thread(self.stop_server)

    def start_server(self):
        if self.server_process is not None:
            raise RuntimeError("Jupyter server is already running")
        
        # 启动 Jupyter server
        self.server_process = pexpect.spawn(
            command="jupyter", 
            args=self.args,
        )
        
        # 等待启动成功的提示信息，它可能包括 token 授权信息
        self.server_process.expect(r"(http://[^:]+:\d+)/\?token=(\w+)", timeout=20)
        print("Jupyter server started successfully.")

        # 抓取启动日志中的 URL，可以用来在测试时访问 Jupyter server
        self.url = self.server_process.match.group(1).decode()
        self.token = self.server_process.match.group(2).decode()
        print(f"Jupyter server started at: {self.url=} with token: {self.token=}")

    def stop_server(self):
        if self.server_process is None:
            raise RuntimeError("Jupyter server is not running")

        self.server_process.sendcontrol('c')  # 发送 Ctrl+C 命令来终止 Jupyter server
        self.server_process.sendline('y')  # 发送 'y' 以确认终止
        try:
            self.server_process.expect(pexpect.EOF, timeout=5)  # 等待进程终止
        except pexpect.exceptions.TIMEOUT:
            self.server_process.terminate(force=True)  # 强制终止进程
        
        print("Jupyter server stopped successfully.")
        self.server_process = None

# 示例使用
if __name__ == '__main__':
    import aiohttp
    import asyncio
    
    async def main():
        with JupyterServerRunner() as runner:
            print(f"{runner.url=}")
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10, connect=3),
                headers={"Authorization": runner.token},
            ) as session:
                async with session.get(
                    runner.url + "/api/",
                ) as response:
                    print(await response.text())

    asyncio.run(main())
        
        
