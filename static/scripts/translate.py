from deep_translator import GoogleTranslator

# 定义翻译器
translator = GoogleTranslator(source='auto', target='en')

# 读取原始文件
input_file = 'all.bio.txt'
output_file = 'english.txt'

# 用于存储已经翻译过的词语，避免重复
translated_words = set()

# 打开输入文件和输出文件
with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for line in infile:
        # 分割每一行的第一列
        word = line.split()[0]
        
        # 如果词语已经翻译过，跳过
        if word in translated_words:
            continue
        
        # 翻译词语
        translated_word = translator.translate(word)
        
        # 将翻译结果写入输出文件
        outfile.write(f"{word}\t{translated_word}\n")
        
        # 将词语添加到已翻译集合中
        translated_words.add(word)

print(f"翻译完成，结果已保存到 {output_file}")