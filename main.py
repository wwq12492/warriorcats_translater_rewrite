import asyncio
import aiohttp
import aiofiles
import csv
import yaml
import os
import sys
from pydantic import ConfigDict,ValidationError
from pydantic_settings import BaseSettings

CONFIG = None # 配置参数

class Config(BaseSettings):
    api_key: str # api密钥
    prompt: str # 提示词，用“|”多行表示，末尾留换行符
    max_connections: int = 4 # 最大并发网络请求量（默认为4）
    output_directory: str # 翻译完成epub输出目录

    model_config = ConfigDict(strict = True,env_file = ".env",env_file_encoding = "utf-8")

if __name__ == "__main__":
    try: # 读取配置文件
        with open("./config.yaml","r",encoding="utf-8") as f:
            CONFIG = Config.model_validate(yaml.safe_load(f)).model_dump()
    except FileNotFoundError:
        print("[错误] 配置文件不存在")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[错误] 配置文件语法错误: {e}")
        sys.exit(1)
    except ValidationError as e:
        print(f"[错误] 配置文件选项错误：{e}")

    print(CONFIG)