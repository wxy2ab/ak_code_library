import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import os
from collections import Counter
from wordcloud import WordCloud
import jieba

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 设置字体路径
if os.name == 'nt':
    font_path = 'C:/Windows/Fonts/msyh.ttc'
elif os.name == 'posix':
    if os.path.exists('/System/Library/Fonts/PingFang.ttc'):
        font_path = '/System/Library/Fonts/PingFang.ttc'
    else:
        font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
else:
    font_path = None

# 设置matplotlib的字体
plt.rcParams['font.sans-serif'] = [font_path, 'Arial Unicode MS', 'Microsoft YaHei', 'SimHei', 'SimSun', 'sans-serif']

# 访问之前步骤的数据
data = cls_telegraph_news

# 1. 词云图
text = ' '.join(data['标题'])
words = jieba.cut(text)
word_counts = Counter(words)
filtered_word_counts = {word: count for word, count in word_counts.items() if count <= 60}
wordcloud = WordCloud(font_path=font_path, width=800, height=400, background_color='white').generate_from_frequencies(filtered_word_counts)
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
wordcloud_file = f"output/{uuid.uuid4()}.png"
plt.savefig(wordcloud_file)
plt.close()

# 2. 使用LLM API进行新闻分析
llm_client = llm_factory.get_instance()

news_batches = []
current_batch = ""
for _, row in data.iterrows():
    news = f"标题: {row['标题']}\n内容: {row['内容']}\n"
    if len(current_batch) + len(news) > 9000:
        news_batches.append(current_batch)
        current_batch = news
    else:
        current_batch += news
if current_batch:
    news_batches.append(current_batch)

analysis_results = []
for batch in news_batches:
    prompt = f"""分析以下新闻，重点关注：
    1. 总结和提炼对市场影响比较大的内容
    2. 金融市场动态总结
    3. 市场情绪的走向和判断
    4. 市场影响、热点和异常
    5. 行业影响、热点和异常
    6. 其他的市场重点要点信息

    新闻内容：
    {batch}
    """
    response = llm_client.one_chat(prompt)
    analysis_results.append(response)

# 准备返回值
results = []
results.append(f"![新闻标题词云图]({wordcloud_file})")
results.append("新闻分析结果：")
for i, result in enumerate(analysis_results, 1):
    results.append(f"批次 {i} 分析：\n{result}\n")

# 将结果保存到analysis_result变量
analysis_result = "\n".join(results)