import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import zipfile
import os
import re
import copy
import json

def get_epub_toc(epub_path):
    book = epub.read_epub(epub_path)
    toc = []

    # 方法1：使用 ebooklib 内置的 TOC
    if book.toc:
        for item in book.toc:
            if isinstance(item, epub.Link):
                # 简单链接（章节）
                toc.append({
                    'title': item.title,
                    'href': item.href.split('#')[0]  # 去掉锚点
                })
            elif isinstance(item, tuple):
                # 有层级的目录（如 Part -> Chapter）
                for sub_item in item[1]:
                    if isinstance(sub_item, epub.Link):
                        toc.append({
                            'title': sub_item.title,
                            'href': sub_item.href.split('#')[0]
                        })
    else:
        # 方法2：尝试从 spine 或文件中找 nav.xhtml
        print("No TOC in book.toc, trying nav.xhtml...")
        return get_toc_from_nav(book)

    return toc

def get_toc_from_nav(book):
    """从 nav.xhtml 中提取目录"""
    toc = []
    for item in book.get_items_of_type(ebooklib.ITEM_NAVIGATION):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        # EPUB3 导航目录通常在 <nav epub:type="toc"> 中
        for nav in soup.find_all('nav', {'epub:type': 'toc'}, recursive=True):
            for a in nav.find_all('a', href=True):
                toc.append({
                    'title': a.get_text().strip(),
                    'href': a['href'].split('#')[0]
                })
        # 备用：找所有 nav 中的链接
        if not toc:
            for a in soup.select('nav a[href]'):
                href = a['href']
                if 'toc' not in href and 'nav' not in href:
                    toc.append({
                        'title': a.get_text().strip(),
                        'href': href.split('#')[0]
                    })
    return toc

def extract_chapter_content(epub_path, toc):
    """
    根据 TOC 提取每一章的正文内容
    :param epub_path: EPUB 文件路径
    :param toc: 目录列表，格式 [{'title': '第一章', 'href': 'chap1.xhtml'}, ...]
    :return: 每章的文本内容列表 [{'title': ..., 'content': ...}, ...]
    """
    results = {}

    with zipfile.ZipFile(epub_path) as z:
        # 获取所有文件名，用于匹配 href
        all_files = {os.path.basename(f): f for f in z.namelist()}

        for chapter in toc:
            href = chapter['href']
            filename = os.path.basename(href)  # 处理路径，如 OEBPS/chap1.xhtml -> chap1.xhtml

            if filename not in all_files:
                print(f"⚠️ 文件未找到: {filename}")
                continue

            try:
                with z.open(all_files[filename],'r') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')

                # 提取正文
                content = extract_text_from_soup(soup)
                results[chapter['title']]=content
            except Exception as e:
                print(f"❌ 解析失败 {filename}: {e}")

    return results

def extract_text_from_soup(soup):
    """
    从 BeautifulSoup 对象中提取干净的正文文本
    """
    
    # 1. 删除不需要的标签
    for tag in soup(['script', 'style', 'nav', 'aside', 'header', 'footer', 'meta', 'link']):
        tag.decompose()

    # 2. 收集所有可能的正文段落
    paragraphs = []
    
    # 常见的正文标签
    for elem in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span']):
        text = elem.get_text(strip=True)
        
        # 过滤：空内容、页码、版权信息、URL
        if not text or len(text) < 2 or re.match(r'^[\d\s\.]+$', text):
            continue
        if any(x in text.lower() for x in ['copyright', '页码', 'chapter', '第 ' + ' 章']):
            continue
        if 'http' in text or '@' in text:
            continue

        # 排除明显是导航或标题的 class
        class_name = ' '.join(elem.get('class', [])).lower()
        if any(kw in class_name for kw in ['nav', 'toc', 'menu', 'header', 'footer', 'footnote']):
            continue

        # 优先保留 <p> 标签，其他标签谨慎处理
        if elem.name == 'p':
            paragraphs.append(text+"\n")
        elif elem.name in ['h1', 'h2', 'h3'] and len(text) < 100:
            # 可能是章节标题，但 TOC 已有，可跳过或保留
            # 这里选择跳过，避免重复
            continue
        elif len(text) > 50:  # 长文本的 div/span 可能是正文
            paragraphs.append(text+"\n")

    return '\n'.join(paragraphs)

def extract_chapters(file):
    toc=get_epub_toc(file)

    contents=extract_chapter_content(file,toc)
    new_dict=copy.deepcopy(contents)
    for a,b in contents.items():
        if not (a=="Prologue" or a[:7]=="Chapter"):
            del new_dict[a]
    
    return new_dict

if __name__ == "__main__":
    with open("/home/dm/test.json","w",encoding="utf-8") as f:
        json.dump(extract_chapters("/media/dm/disk/其他/书籍/猫武士/第9季 Changing Skies 天之变/Warriors Changing Skies 1 the Elders Quest (Erin Hunter) (Z-Library).epub"),f)