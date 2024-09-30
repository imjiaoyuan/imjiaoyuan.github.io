import os
import re
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# 定义一个函数来提取 title 和 date
def extract_title_and_date(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    match = re.search(r'title: (.*)\ndate: (.*)', content)
    if match:
        title = match.group(1).strip()
        date = match.group(2).strip()
        return title, date
    return None, None

# 遍历 posts 目录下的所有 .md 文件
entries = []
for filename in os.listdir('posts'):
    if filename.endswith('.md') and filename != 'toc.md':
        title, date = extract_title_and_date(os.path.join('posts', filename))
        if title and date:
            entries.append((date, title, filename))

# 按照 date 进行降序排序
entries.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=True)

# 生成 README.md 文件
with open('README.md', 'r', encoding='utf-8') as readme_file:
    readme_content = readme_file.read()

# 找到 ### Posts 标题的位置
posts_index = readme_content.find('### Posts')
if posts_index != -1:
    # 保留 ### Posts 标题前的内容
    readme_content = readme_content[:posts_index]
else:
    # 如果 ### Posts 标题不存在，则添加一个
    readme_content += '### Posts\n\n'

# 写入目录
with open('README.md', 'w', encoding='utf-8') as readme_file:
    readme_file.write(readme_content)
    readme_file.write('### Posts\n\n')
    
    current_year = None
    for date, title, filename in entries:
        year = date.split('-')[0]
        if year != current_year:
            if current_year is not None:
                readme_file.write('\n')  # 在年份上方添加一个换行符
            current_year = year
            readme_file.write(f'**{current_year}**\n\n')
        # 构建链接
        link = f"- [{title}](posts/{filename.replace('.md', '.html')}) / {date}"
        # 写入 README.md 文件
        readme_file.write(link + '\n')
    readme_file.write('\n')  # 在年份下方添加一个换行符

print("README.md has been updated.")

# 生成 RSS 文件
rss = Element('rss', {'version': '2.0'})
channel = SubElement(rss, 'channel')

# 添加频道信息
title = SubElement(channel, 'title')
title.text = "JiaoYuan's Blog"
link = SubElement(channel, 'link')
link.text = 'https://yuanj.top'
description = SubElement(channel, 'description')
description.text = '思绪来得快去得也快，偶尔会在这里停留'

# 添加文章条目
for date, title_text, filename in entries:
    item = SubElement(channel, 'item')
    title = SubElement(item, 'title')
    title.text = title_text
    link = SubElement(item, 'link')
    link.text = f'https://yuanj.top/posts/{filename.replace(".md", ".html")}'
    pubDate = SubElement(item, 'pubDate')
    pubDate.text = datetime.strptime(date, '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 GMT')
    description = SubElement(item, 'description')
    description.text = f'{title_text} - {date}'

# 将 XML 树转换为字符串并美化输出
xml_str = tostring(rss, 'utf-8')
parsed_xml = minidom.parseString(xml_str)
pretty_xml_str = parsed_xml.toprettyxml(indent="  ")

# 写入 RSS 文件
with open('rss.xml', 'w', encoding='utf-8') as rss_file:
    rss_file.write(pretty_xml_str)

print("RSS file has been generated.")