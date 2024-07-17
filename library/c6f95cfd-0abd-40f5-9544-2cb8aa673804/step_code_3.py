from matplotlib import font_manager
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
import re
import uuid
import os
from collections import Counter

os.makedirs('output', exist_ok=True)

df = cailian_api_news

def preprocess_text(text):
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    words = jieba.cut(text)
    stop_words = set(['的', '了', '在', '是', '和', '与', '及', '或', '等', '也', '而', '但', '还', '只', '就'])
    return [word for word in words if word not in stop_words and len(word) > 1]

all_words = []
for _, row in df.iterrows():
    all_words.extend(preprocess_text(row['新闻标题'] + row['新闻内容']))

word_freq = Counter(all_words)
filtered_words = {word: freq for word, freq in word_freq.items() if freq <= 60}

if os.name == 'nt':
    font_path = 'C:/Windows/Fonts/msyh.ttc'
elif os.name == 'posix':
    if os.path.exists('/System/Library/Fonts/PingFang.ttc'):
        font_path = '/System/Library/Fonts/PingFang.ttc'
    else:
        font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
else:
    font_path = None

wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=font_path, max_words=100).generate_from_frequencies(filtered_words)
def configure_matplotlib_for_chinese():
    import platform
    system = platform.system()
    if system == 'Windows':
        font_name = 'SimHei'
    elif system == 'Darwin':
        font_name = 'STHeiti'
    else:  # For Linux
        font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
        if os.path.exists(font_path):
            font_manager.fontManager.addfont(font_path)
            font_name = font_manager.FontProperties(fname=font_path).get_name()
        else:
            raise FileNotFoundError(f"Font file not found: {font_path}")
    
    # Set the font properties
    plt.rcParams['font.sans-serif'] = [font_name]
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.unicode_minus'] = False

# 运行配置函数
configure_matplotlib_for_chinese()

plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
file_name = f"output/{uuid.uuid4()}.png"
plt.tight_layout(pad=0)
plt.savefig(file_name, dpi=300, bbox_inches='tight')
plt.close()

top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:20]

results = []
results.append(f"![词云图]({file_name})")
results.append("主要发现：")
results.append("1. 词云图已生成，展示了新闻内容中最常见的关键词。")
results.append("2. 出现频率最高的20个词（频率不超过60）：")
for word, freq in top_words:
    results.append(f"   - {word}: {freq}")
results.append("3. 这些高频词反映了新闻报道的主要关注点和热点话题。")

analysis_result = "\n".join(results)