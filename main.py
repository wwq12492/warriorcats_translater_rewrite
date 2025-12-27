import asyncio
import aiohttp
import aiofiles
import csv
import os
from pathlib import Path
import argparse
import yaml
import sys
from modules.schema import Config,CliArgs
from pydantic import ValidationError

CONFIG = None # 配置参数

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
    parser.add_argument("translate_file",nargs="+",help="待翻译单文件名/文件列表，或者一个包含文件路径列表的txt")
    args = CliArgs.model_validate(vars(parser.parse_args())).model_dump()

    # diff待翻译文件列表和cache,删除无用cache
    cache_path = Path("./cache").expanduser().resolve()
    if cache_path.exists():
        # 获取所有文件和目录
        for item in cache_path.iterdir():
            if item.is_file() and item.suffix == ".json":
                flag = True # 是否删除
                for compare in args["translate_file"]:
                    if Path(compare).stem == item.stem:
                        flag = False
                if flag == True:
                    item.unlink()
            else:
                item.unlink() # 可能无法删除目录
    else:
        cache_path.mkdir()
