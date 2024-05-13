from client import JupyterServerClient

if __name__ == "__main__":
    import asyncio

    from rich import print

    async def test():
        async with JupyterServerClient("http://localhost:9999") as client:
            print(await client.api())

            # print("创建 session", await client.create_session(), "\n")

            session_list = await client.get_sessions()
            print("获取 session 列表", session_list, "\n")

            print("获取 session", await client.get_session(session_list[0]["id"]), "\n")

            # print("删除 session", await client.delete_session(session_list[0]["id"]), "\n")

    asyncio.run(test())
