import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import os
from collections import Counter
from datetime import datetime

os.makedirs('output', exist_ok=True)

df = cailian_api_news

def analyze_news_batch(news_batch):
    llm_client = llm_factory.get_instance()
    prompt = f"""分析以下新闻内容，重点关注：
    1. 总结和提炼对市场影响比较大的内容
    2. 金融市场动态总结
    3. 市场情绪的走向和判断
    4. 市场热点和异常
    5. 其他的市场重点要点信息

    新闻内容：
    {news_batch}
    """
    return llm_client.one_chat(prompt)

news_batches = []
current_batch = ""
for _, row in df.iterrows():
    if len(current_batch) + len(row['新闻内容']) > 9500:
        news_batches.append(current_batch)
        current_batch = row['新闻内容']
    else:
        current_batch += "\n" + row['新闻内容']
if current_batch:
    news_batches.append(current_batch)

analysis_results = []
for batch in news_batches:
    analysis_results.append(analyze_news_batch(batch))

df['发布时间'] = pd.to_datetime(df['发布时间'])
df['日期'] = df['发布时间'].dt.date

news_count_by_date = df['日期'].value_counts().sort_index()
if os.name == 'nt':
    font_path = 'C:/Windows/Fonts/msyh.ttc'
elif os.name == 'posix':
    if os.path.exists('/System/Library/Fonts/PingFang.ttc'):
        font_path = '/System/Library/Fonts/PingFang.ttc'
    else:
        font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
else:
    font_path = None
plt.rcParams['font.sans-serif'] = [font_path,'Arial Unicode MS', 'Microsoft YaHei', 'SimHei', 'SimSun', 'sans-serif']
plt.figure(figsize=(12, 6))
news_count_by_date.plot(kind='bar')
plt.title('每日新闻数量')
plt.xlabel('日期')
plt.ylabel('新闻数量')
plt.xticks(rotation=45)
file_name = f"output/{uuid.uuid4()}.png"
plt.tight_layout()
plt.savefig(file_name)
plt.close()

source_counts = df['文章来源'].value_counts()
plt.figure(figsize=(10, 6))
source_counts.plot(kind='pie', autopct='%1.1f%%')
plt.title('新闻来源分布')
file_name2 = f"output/{uuid.uuid4()}.png"
plt.tight_layout()
plt.savefig(file_name2)
plt.close()

all_words = ' '.join(df['新闻标题']).split()
word_freq = Counter(all_words)
common_words = dict(word_freq.most_common(20))
plt.figure(figsize=(12, 6))
plt.bar(common_words.keys(), common_words.values())
plt.title('新闻标题中最常见的20个词')
plt.xticks(rotation=45, ha='right')
file_name3 = f"output/{uuid.uuid4()}.png"
plt.tight_layout()
plt.savefig(file_name3)
plt.close()

results = []
results.append(f"![每日新闻数量]({file_name})")
results.append(f"![新闻来源分布]({file_name2})")
results.append(f"![新闻标题常见词]({file_name3})")
results.append("主要发现：")
results.append("1. 新闻数量分布：" + str(news_count_by_date.to_dict()))
results.append("2. 主要新闻来源：" + ", ".join(source_counts.index[:5]))
results.append("3. 新闻标题常见词：" + ", ".join(list(common_words.keys())[:10]))
results.append("\nLLM分析结果：")
for i, result in enumerate(analysis_results, 1):
    results.append(f"批次{i}分析：\n{result}")

analysis_result = "\n".join(results)