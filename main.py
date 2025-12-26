import asyncio
import aiohttp
import aiofiles
import csv
from pathlib import Path
import os
import argparse
import yaml
import sys
from pydantic import ConfigDict,ValidationError,Field,BaseModel,field_validator
from pydantic_settings import BaseSettings

CONFIG = None # 配置参数

# 配置文件校验
class Config(BaseSettings):
    api_key: str = Field(description = "api密钥")
    prompt: str = Field(description = "提示词，用“|”多行表示，末尾留换行符")
    max_connections: int = Field(default=4,description="最大并发网络请求量（默认为4）")
    output_directory: str = Field(description="翻译完成epub输出目录")

    @field_validator("output_directory")
    @classmethod
    def validate_output_directory(cls, path: str) -> str:
        resolved_path = Path(path).expanduser().resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(f"路径不存在: {resolved_path}")
        
        if not resolved_path.is_dir():
            raise NotADirectoryError(f"不是目录: {resolved_path}")
        
        # 验证读权限
        if not os.access(resolved_path, os.R_OK):
            raise PermissionError(f"无读权限: {resolved_path}")
        
        return str(resolved_path)

    model_config = ConfigDict(strict = True,env_file = ".env",env_file_encoding = "utf-8")

# 输入参数教研
class CliArgs(BaseModel):
    translate_file: list[str] = Field(description="待翻译的单文件路径/文件路径列表，或者一个由换行隔开的文件路径列表txt文件路径")
    
    @field_validator("translate_file")
    @classmethod
    def validate_translate_files(cls, v: list[str]) -> list[str]:
        if len(v)==1:
            resolved_path = Path(v[0]).expanduser().resolve() # 解析路径为标准路径
            
            if not resolved_path.exists():
                    raise FileNotFoundError(f"路径不存在: {resolved_path}")
                
            # 验证读权限
            if not os.access(resolved_path, os.R_OK):
                raise PermissionError(f"无读权限: {resolved_path}")
            
            if resolved_path.suffix==".txt":
                txt_pathlist = None
                with open(resolved_path,"r",encoding="utf-8") as f:
                    txt_pathlist = f.read().splitlines()
                
                for path in txt_pathlist:
                    resolved_path = Path(path).expanduser().resolve() # 解析路径为标准路径
                    
                    if resolved_path.suffix != ".epub":
                        raise ValueError("文件类型错误：只支持epub")

                    if not resolved_path.exists():
                        raise FileNotFoundError(f"路径不存在: {resolved_path}")
                    
                    # 验证读权限
                    if not os.access(resolved_path, os.R_OK):
                        raise PermissionError(f"无读权限: {resolved_path}")
                
            elif resolved_path.suffix==".epub":
                pass
            else:
                raise ValueError("文件类型错误：不是epub/txt列表")
        else:
            for path in v:
                resolved_path = Path(path).expanduser().resolve() # 解析路径为标准路径
                
                if resolved_path.suffix != ".epub":
                    raise ValueError("文件类型错误：只支持epub")

                if not resolved_path.exists():
                    raise FileNotFoundError(f"路径不存在: {resolved_path}")
                
                # 验证读权限
                if not os.access(resolved_path, os.R_OK):
                    raise PermissionError(f"无读权限: {resolved_path}")

        return v

    model_config = ConfigDict(strict = True)

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

    print(args["translate_file"])
