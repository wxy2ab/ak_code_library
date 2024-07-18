import pandas as pd
import uuid
import os

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 访问之前步骤的数据
data = futu_news_flash

# 准备新闻文本进行分析
news_texts = []
total_length = 0
batch = []

for _, row in data.iterrows():
    news = f"标题: {row['标题']}\n内容: {row['内容']}\n发布时间: {row['发布时间']}\n\n"
    if total_length + len(news) > 9500:  # 留有余地
        news_texts.append("".join(batch))
        batch = [news]
        total_length = len(news)
    else:
        batch.append(news)
        total_length += len(news)

if batch:
    news_texts.append("".join(batch))

# 使用LLM API进行新闻分析
llm_client = llm_factory.get_instance()
analysis_results = []

for text in news_texts:
    prompt = f"""分析以下新闻，并提供以下方面的见解：
    0. 执行概况（新闻时间段，条目数，范围）
    1. 总结和提炼对市场影响比较大的内容
    2. 金融市场动态总结
    3. 市场情绪的走向和判断
    4. 市场影响、热点和异常
    5. 行业影响、热点和异常
    6. 其他的市场重点要点信息

    新闻内容：
    {text}
    """
    response = llm_client.one_chat(prompt)
    analysis_results.append(response)

# 准备返回值
results = []
results.append("# 富途牛牛快讯分析报告")
results.append("\n## 新闻分析结果")

for i, result in enumerate(analysis_results, 1):
    results.append(f"\n### 批次 {i} 分析")
    results.append(result)

results.append("\n## 总结")
summary_prompt = f"基于以下分析结果，总结富途牛牛快讯的主要发现和市场影响：\n\n{''.join(analysis_results)}"
summary = llm_client.one_chat(summary_prompt)
results.append(summary)

# 将结果保存到analysis_result变量
analysis_result = "\n".join(results)