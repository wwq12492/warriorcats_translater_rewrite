import asyncio
import aiohttp
import aiofiles
import csv
import yaml
import os
import sys
from pydantic import BaseModel

class Config(BaseModel):
    api_key: str # api密钥
    prompt: str # 提示词，用“|”多行表示，末尾留换行符
    max_connections: int | None # 最大并发网络请求量（默认为4）
    output_directory: str | None # 翻译完成epub输出目录（默认为程序所在目录下）

if __name__ == "__main__":
    CONFIG = None # 配置参数

    try: # 读取配置文件
        with open("./config.yaml","r",encoding="utf-8") as f:
            CONFIG = yaml.safe_load(f)
    except FileNotFoundError:
        print("[错误] 配置文件不存在")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[错误] 配置文件格式错误: {e}")
        sys.exit(1)

    print(CONFIG)