from client import JupyterServerClient

if __name__ == "__main__":
    import asyncio

    from rich import print

    async def test():
        async with JupyterServerClient("http://localhost:9999") as client:
            print(await client.api())

            print("获取 spec", await client.get_kernelspecs(), "\n")

            # print("创建 kernel", await client.start_a_kernel(), "\n")

            # kernel_list = await client.get_kernels()
            # print("获取 kernel 列表", kernel_list, "\n")

            # print("获取 kernel", await client.get_kernel(kernel_list[0]["id"]), "\n")

            # print("删除 kernel", await client.delete_kernel(kernel_list[0]["id"]), "\n")

    asyncio.run(test())
