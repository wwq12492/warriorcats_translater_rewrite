import asyncio
import aiohttp
import aiofiles
import csv
import os
from pathlib import Path
import argparse
import yaml
import sys
from pydantic import ValidationError
import json

from modules.schema import Config,CliArgs
from modules.epub_read import extract_chapters

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
    args = CliArgs.model_validate(vars(parser.parse_args())).model_dump() # 结果为{arg1:[...],...}，不要直接遍历！

    # diff待翻译文件列表和cache,删除无用cache
    cache_path = Path("./cache").expanduser().resolve()
    if cache_path.exists():
        # 获取所有文件和目录
        for item in cache_path.iterdir():
            if item.is_file() and item.suffix == ".json": # 必须是json
                flag = True # 是否删除
                for compare in args["translate_file"]: # 将当前文件和需要的文件列表比对，如果没有匹配的，就会被删除
                    if Path(compare).stem == item.stem:
                        flag = False
                if flag == True:
                    item.unlink()
            else:
                item.unlink() # 潜在错误：可能无法删除目录！
    else:
        cache_path.mkdir()

    # 读取epub数据并且筛选需要翻译的章节
    data_to_translate: dict[str, dict] = {} # 剩下的都是要翻译的内容

    for item in args["translate_file"]:
        data_to_translate[str(Path(item).stem)] = extract_chapters(str(Path(item).expanduser().resolve())) # 获取 {chapter: content,...}格式的单本书数据，并且存入待翻译序列

    for item in Path("./cache").iterdir(): # 遍历所有已经存在的cache
        with open(str(item)) as f:
            data: dict[str,str] = json.load(f)
            for chapter,content in data.items(): # 如果有这本书（这个cache文件）的这个章节，删除data_to_translate中对应书的章节
                if chapter in data_to_translate[item.stem]:
                    del data_to_translate[item.stem][chapter]
        if data_to_translate[item.stem] == {}:
            del data_to_translate[item.stem] # 如果正本书都被“删完”（全部缓存完成）了，直接删除这个书在data_to_translate中的key