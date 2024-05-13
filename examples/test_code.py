from client import JupyterServerClient

if __name__ == "__main__":
    import asyncio

    from rich import print

    async def test():
        async with JupyterServerClient("http://localhost:9999") as client:
            print(await client.api())

            kernel_info = await client.start_a_kernel()
            print("创建 kernel", kernel_info, "\n")

            # print("删除 kernel", await client.delete_kernel(kernel_list[0]["id"]), "\n")

    asyncio.run(test())
