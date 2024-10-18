import os
import re
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def extract_title_and_date(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    match = re.search(r'title: (.*)\ndate: (.*)', content)
    if match:
        title = match.group(1).strip()
        date = match.group(2).strip()
        return title, date
    return None, None

entries = []
for filename in os.listdir('posts'):
    if filename.endswith('.md') and filename != 'toc.md':
        title, date = extract_title_and_date(os.path.join('posts', filename))
        if title and date:
            entries.append((date, title, filename))

entries.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=True)


with open('toc.md', 'r', encoding='utf-8') as readme_file:
    readme_content = readme_file.read()

posts_index = readme_content.find('### Posts')
if posts_index != -1:
    readme_content = readme_content[:posts_index]
else:
    readme_content += '### Posts\n\n'

with open('toc.md', 'w', encoding='utf-8') as readme_file:
    readme_file.write(readme_content)
    readme_file.write('### Posts\n\n')
    
    current_year = None
    for date, title, filename in entries:
        year = date.split('-')[0]
        if year != current_year:
            if current_year is not None:
                readme_file.write('\n')
            current_year = year
            readme_file.write(f'**{current_year}**\n\n')
        link = f"- [{title}](posts/{filename.replace('.md', '.html')}) / {date}"
        readme_file.write(link + '\n')
    readme_file.write('\n')

print("toc.md has been updated.")
rss = Element('rss', {'version': '2.0'})
channel = SubElement(rss, 'channel')

title = SubElement(channel, 'title')
title.text = "JiaoYuan's Blog"
link = SubElement(channel, 'link')
link.text = 'https://yuanj.top'
description = SubElement(channel, 'description')
description.text = '思绪来得快去得也快，偶尔会在这里停留'

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

xml_str = tostring(rss, 'utf-8')
parsed_xml = minidom.parseString(xml_str)
pretty_xml_str = parsed_xml.toprettyxml(indent="  ")

with open('rss.xml', 'w', encoding='utf-8') as rss_file:
    rss_file.write(pretty_xml_str)
print("RSS file has been generated.")

with open('README.md', 'r', encoding='utf-8') as readme_file:
    readme_content = readme_file.read()

latest_posts_index = readme_content.find('### Posts')
if latest_posts_index != -1:
    readme_content = readme_content[:latest_posts_index]
else:
    readme_content += '### Posts\n\n'

with open('README.md', 'w', encoding='utf-8') as readme_file:
    readme_file.write(readme_content)
    readme_file.write('### Posts\n\n')
    
    for i in range(min(5, len(entries))):
        date, title, filename = entries[i]
        link = f"- [{title}](posts/{filename.replace('.md', '.html')}) / {date}"
        readme_file.write(link + '\n')
    
    readme_file.write('- [All Posts](./toc.md) / [RSS](https://yuanj.top/rss.xml)\n')

print("README.md has been updated with the Posts.")