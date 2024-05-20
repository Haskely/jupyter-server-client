from jupyter_server_client import JupyterServerClient

example_code = """
print('hello world')

from tqdm import tqdm
import time

for _ in tqdm(range(5)):
    time.sleep(0.2)

print('done')
"""

if __name__ == "__main__":
    import asyncio

    from rich import print

    async def test():
        async with JupyterServerClient("http://127.0.0.1:8888") as client:
            print(await client.api())

            kernel_info = await client.start_a_kernel()
            print("创建 kernel", kernel_info, "\n")

            kernel_list = await client.get_kernels()
            print("获取 kernel 列表", kernel_list, "\n")

            print("获取 kernel", await client.get_kernel(kernel_list[0]["id"]), "\n")

            print("获取 spec", await client.get_kernelspecs(), "\n")

            print(f"执行代码:{example_code}")
            async with client.connect_kernel(kernel_info["id"]) as kernel:
                await kernel.execute(example_code)
                print()

            print("删除 kernel", await client.delete_kernel(kernel_info["id"]), "\n")

    asyncio.run(test())
