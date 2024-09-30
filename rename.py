import os
import re
from deep_translator import GoogleTranslator

# 初始化翻译器
translator = GoogleTranslator(source='zh-CN', target='en')

# 遍历当前目录下的所有 .md 文件
for filename in os.listdir('.'):
    if filename.endswith('.md'):
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()

        # 使用正则表达式提取 title 和 date
        match = re.search(r'title: (.*)\ndate: (.*)', content)
        if match:
            title = match.group(1).strip()
            date = match.group(2).strip()

            # 翻译 title 为英文
            translated_title = translator.translate(title)

            # 将空格和除了 - 以外的所有字符替换为 -
            translated_title = re.sub(r'[^a-zA-Z0-9-]', '-', translated_title)

            # 将连续的 - 替换为一个 -
            translated_title = re.sub(r'-+', '-', translated_title)

            # 去除开头和结尾的 -
            translated_title = translated_title.strip('-')

            # 将所有字母转换为小写
            translated_title = translated_title.lower()

            # 构建新的文件名
            new_filename = f"{date}-{translated_title}.md"

            # 重命名文件
            os.rename(filename, new_filename)
            print(f"Renamed {filename} to {new_filename}")

print("All files have been renamed.")