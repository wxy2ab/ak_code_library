import pandas as pd
import uuid
import os

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 访问之前步骤的数据
data = sina_global_financial_news

# 准备新闻内容进行分析
news_content = ""
for _, row in data.iterrows():
    news_content += f"{row['时间']}: {row['内容']}\n\n"

# 使用LLM API进行新闻分析
llm_client = llm_factory.get_instance()

prompt = f"""分析以下全球财经快讯内容，请按照以下要点进行总结：
0. 执行概况(新闻时间段，条目数，范围)
1. 总结和提炼对市场影响比较大的内容
2. 金融市场动态总结
3. 市场情绪的走向和判断
4. 市场影响、热点和异常
5. 行业影响、热点和异常
6. 其他的市场重点要点信息

新闻内容：
{news_content}
"""

response = llm_client.one_chat(prompt)

# 准备返回值
results = []
results.append("# 全球财经快讯分析报告")
results.append(response)

# 将结果保存到analysis_result变量
analysis_result = "\n\n".join(results)