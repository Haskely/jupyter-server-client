from client import JupyterServerClient

if __name__ == "__main__":
    import asyncio

    from rich import print

    async def test():
        async with JupyterServerClient("http://localhost:9999") as client:
            print(await client.api())

            # print("创建绝对路径文件夹", await client.create_dir("/data")) # 404

            # print("创建相对路径文件夹", await client.create_dir("data2"))

            # print("创建多级路径文件夹", await client.create_dir("data3/data4/data5")) # 500

            # print("创建文件夹", await client.create_dir("data"))

            # print("上传目录不存在文件", await client.upload_file("non_exist_dir/my_file.txt", "hello world", "text")) # 500

            # print("上传文件", await client.upload_file("data/my_file.txt", "hello world", "text"))

            # print("获取文件列表", await client.get_file("data"))

            # print("获取文件", await client.get_file_or_dir("data/my_file.txt"))

            # with open("/data/nova/scripts/jupyter_server_study/jupyter_workdir/24.png", "rb") as f:
            #     _bytes = f.read()
            # print("上传二进制文件", await client.upload_file("data/24.png", base64.b64encode(_bytes).decode('utf-8'), "base64"), "\n")

            # print(await client.get_file_or_dir("data/24.png"))

            print("删除文件", await client.delete_file("data/my_file.txt"))

    asyncio.run(test())
