import asyncio
import aiohttp
import aiofiles
import csv
import os
import argparse
import yaml
import sys
from pydantic import ConfigDict,ValidationError,Field
from pydantic_settings import BaseSettings

CONFIG = None # 配置参数

class Config(BaseSettings):
    api_key: str = Field(description = "api密钥")
    prompt: str = Field(description = "提示词，用“|”多行表示，末尾留换行符")
    max_connections: int = Field(default=4,description="最大并发网络请求量（默认为4）")
    output_directory: str = Field(description="翻译完成epub输出目录")

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
        print(f"[错误] 配置文件选项错误：")
        for error in e.errors():
            error_location: str = ""
            for item in error["loc"]:
                error_location += "/"+str(item) # 生成/arg1/arg2/...格式的错误路径

            print(f"选项 {error_location} (用户输入：{error['input']}) 错误: {error['msg']}")

    # epub读取（翻译数据准备）
    parser = argparse.ArgumentParser(description="A Warrior Cats novel translater")
    parser.add_argument("file",nargs="+",help="待翻译单文件名/文件列表，或者一个包含文件路径列表的txt")
    args = parser.parse_args()

    print(args.file)
