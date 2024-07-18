import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import os
from datetime import datetime

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 访问之前步骤的数据
df = eastmoney_global_financial_news

# 数据预处理
df['发布时间'] = pd.to_datetime(df['发布时间'])
df = df.sort_values('发布时间')

# 执行概况
start_date = df['发布时间'].min().strftime('%Y-%m-%d %H:%M:%S')
end_date = df['发布时间'].max().strftime('%Y-%m-%d %H:%M:%S')
news_count = len(df)

# 准备新闻文本进行LLM分析
news_texts = []
current_batch = ""
for _, row in df.iterrows():
    news_item = f"标题: {row['标题']}\n摘要: {row['摘要']}\n发布时间: {row['发布时间']}\n\n"
    if len(current_batch) + len(news_item) > 9500:
        news_texts.append(current_batch)
        current_batch = news_item
    else:
        current_batch += news_item
if current_batch:
    news_texts.append(current_batch)

# 使用LLM API进行新闻分析
llm_client = llm_factory.get_instance()
analysis_results = []

for i, text_batch in enumerate(news_texts):
    prompt = f"""分析以下全球财经快讯内容，重点关注：
    1. 总结和提炼对市场影响比较大的内容
    2. 金融市场动态总结
    3. 市场情绪的走向和判断
    4. 市场影响、热点和异常
    5. 行业影响、热点和异常
    6. 其他的市场重点要点信息

    新闻内容：
    {text_batch}
    """
    response = llm_client.one_chat(prompt)
    analysis_results.append(response)

# 合并分析结果
combined_analysis = "\n".join(analysis_results)

# 准备返回值
results = []
results.append(f"执行概况：")
results.append(f"- 新闻时间段：{start_date} 至 {end_date}")
results.append(f"- 新闻条目数：{news_count}")
results.append(f"- 新闻范围：全球财经快讯")
results.append("\n新闻分析结果：")
results.append(combined_analysis)

# 将结果保存到analysis_result变量
analysis_result = "\n".join(results)