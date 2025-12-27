from pydantic import ConfigDict,Field,BaseModel,field_validator
from pydantic_settings import BaseSettings
import sys
import os
from pathlib import Path

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

# 输入参数校验
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
                    filedata = f.read()
                    if not filedata.strip():
                        raise ValueError("文件列表为空")
                    
                    txt_pathlist = [item for item in filedata.splitlines() if item.strip()]
                
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