# 猫武士翻译脚本（重构版）
## 核心更新
- aiofiles异步epub文件操作
- 重写的通用epub解析器（需要阅读**epub官方文档范式**）
- 翻译逻辑优化（ai标记专有名词 → 手动+ai发现+缓存）
- 面向对象编程
- 更好的异常处理
- 数据结构、缓存设计和工作流优化（分书缓存文件，yaml方便编写，自动打开编辑器保存确认）
- sys实现翻译参数的传入（不用所有东西都写在config里，比如要翻译的书）

### 专有名词替换
#### 逻辑
1. 依据`glossary.csv`的内容先将**已知的专有名词替换成已知中文**并且用**大括号和特殊字符标记**
2. 给ai提供system_prompt，要求不翻译已标记的专有名词，同时**发现新的专有名词**标记出并且保留英文
3. 返回的结果立即去除`{ᏇᎢ__xxxxxxxx__ᎢᏇ}`样式
4. 手动替换阶段ai新发现的词汇征求用户对应译文之后创建对应中英文对照键值对并且存入`glossary.csv`

> 更新差异：`glossary.csv`（原`translate_dict.json`）在手动替换新的专有名词过程中不发挥作用，只是被扩充。他只在初始的已知专有名词替换和标记标记阶段被用于匹配已知专有名词

#### prompt设计
```markdown
你正在将英文小说《猫武士》系列翻译为中文。请严格遵循以下规则：

### 术语处理规则
1. **特殊标识保留**
   - 格式为由大括号包裹的如示例 `{ᏇᎢ__xxxxxxxx__ᎢᏇ}` 的文本是受保护术语，**原样保留不翻译**
   - 示例：`{ᏇᎢ__火星__ᎢᏇ}` → 保持原样

2. **专有名词处理**
   - 猫名：保留英文原名，用{}标记
     - 示例：Firestar → {Firestar}
     - 示例：Brambleclaw → {Brambleclaw}
   
   - 族群名：保留英文原名，用{}标记
     - 示例：ThunderClan → {ThunderClan}
     - 示例：StarClan → {StarClan}
     - 示例：the Sisters → {the Sisters}
   
   - 地名/物品名：保留英文原名，用{}标记
     - 示例：Twoleg → {Twoleg}
     - 示例：Thunder Path → {Thunder Path}
     - 示例：Moonstone → {Moonstone}
   
   - 仪式/头衔：保留英文原名，用{}标记
     - 示例：medicine cat → {medicine cat}
     - 示例：deputy → {deputy}

3. **翻译风格要求**
   - 猫的称呼：用"只"而非"个"，如"一只灰猫"
   - 动作描写：用猫科动物的自然动作
   - 对话翻译：符合中文口语习惯，避免生硬直译
   - 战斗场面：简洁有力，多用短句

4. **格式要求**
   - 输出纯译文，**不要**加任何引导语、结束语
   - 段落结构保持与原文一致
   - 对话前的破折号保持为"——"

### 核心语言翻译要求
1. 保持奇幻文学风格，用词符合动物视角叙事
2. 猫的对话要自然生动，避免过度拟人化
3. 描述战斗、狩猎、仪式时要生动有力

### 翻译示例
原文: "Firestar looked at Graystripe, his friend from ThunderClan."
翻译: "{Firestar}看向{Graystripe}，他在{ThunderClan}的朋友。"

原文: "The Twoleg monster raced down the Thunder Path."
翻译: {Twoleg}怪兽沿着{Thunder Path}疾驰而去。

请开始翻译以下内容：
```

## 脚本参数和config options
### 可用参数
```bash
python3 ./main.py [file / file1 file2 file3 ... / file_list.txt]
```

### 配置文件格式
```yaml
api_key: "string" 
prompt: | 
  string
max_connections: 0 
output_directory: "string"
# 待完善&分类
```

## 项目结构
```
warriorcats_translator_rewrite/
│
├── main.py                    # 主脚本（唯一需要执行的）
├── config.yaml                     # 配置文件
├── glossary.csv                    # 术语表（CSV易编辑）
├── README.md                       # 使用说明
├── LICENSE
└── cache/                          # 缓存目录（自动创建）
    ├── bookA.json
    ├── bookB.json
    └── bookC.json
```

## 用户工作流
### 前置步骤
1. 填写`config.yaml`
2. 准备待翻译epub（*可选*：也准备一个epub文件列表`listname.txt`，每本书路径一行一个，传递给脚本）

### 初步翻译
1. 比较新输入待翻译文件和已有cache的**diff**，**删除无意义cache文件**
2. 比较检查cache是否是“完成”的（要求翻译的书是否有对应的cache文件，文件的章节和书的章节是否匹配），用于区分**进入手动专有名词替换（完备）/打断后从断点重新开始（缺少）**
3. 翻译缓存写入时，**缺少翻译文件就创建，缺少对应章节数据就写入对应章节所在书的对应cache文件**
4. 完成后退出程序，提示`“初步翻译完成，检查cache并修改，重新执行程序（小幅度修改cache数据中一些ai回答的瑕疵/删除这个某组章节键值对/删除对应的cache文件，会导致这些章节/书在二次运行脚本时被重翻译）”`

### 手动检查cache
1. 小幅度修改cache数据中一些ai回答的瑕疵
2. 删除这个某组章节键值对/删除对应的cache文件，会导致这些章节/书在二次运行脚本时因为机制被**重翻译**

### 手动专有名词替换
1. 识别`{}`格式的专有名词,从`glossary.csv`匹配，如果没有对应方案，记录并打印出列表要求用户替换，结束程序
2. 用户编辑csv文件，写入列出的新的没有替换方案的专有名词的对应替换方案（**声明式替换方法**，而非问答式命令替换），重新运行程序
3. 自动替换专有名词，输出epub到指定目录

## 相关子项目
专有名词`translate_dict`构建爬虫，从wiki抓取猫名、地名等构建基本的`translate_dict`