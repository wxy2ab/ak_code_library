import pandas as pd
import uuid
import os

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 访问之前步骤的数据
data = ths_global_financial_live

# 准备进行新闻分析
llm_client = llm_factory.get_instance()

# 初始化结果列表
results = []

# 执行概况
news_count = len(data)
time_range = f"{data['发布时间'].min()} 到 {data['发布时间'].max()}"
results.append(f"执行概况：分析了{news_count}条新闻，时间范围从{time_range}")

# 分批处理新闻内容
batch_content = ""
batch_number = 1

for _, row in data.iterrows():
    news_item = f"标题：{row['标题']}\n内容：{row['内容']}\n发布时间：{row['发布时间']}\n\n"
    if len(batch_content) + len(news_item) > 9500:  # 留有余地
        prompt = f"""分析以下新闻批次{batch_number}，关注以下要点：
1. 总结和提炼对市场影响比较大的内容
2. 金融市场动态总结
3. 市场情绪的走向和判断
4. 市场影响、热点和异常
5. 行业影响、热点和异常
6. 其他的市场重点要点信息

新闻内容：
{batch_content}
"""
        response = llm_client.one_chat(prompt)
        results.append(f"批次{batch_number}分析结果：\n{response}")
        batch_content = news_item
        batch_number += 1
    else:
        batch_content += news_item

# 处理最后一批
if batch_content:
    prompt = f"""分析以下新闻批次{batch_number}，关注以下要点：
1. 总结和提炼对市场影响比较大的内容
2. 金融市场动态总结
3. 市场情绪的走向和判断
4. 市场影响、热点和异常
5. 行业影响、热点和异常
6. 其他的市场重点要点信息

新闻内容：
{batch_content}
"""
    response = llm_client.one_chat(prompt)
    results.append(f"批次{batch_number}分析结果：\n{response}")

# 总结分析
summary_prompt = f"""根据以下分批次的新闻分析结果，给出一个总体的市场分析总结，包括：
1. 市场整体情况
2. 主要热点和趋势
3. 市场情绪评估
4. 潜在的市场机会和风险

分析结果：
{''.join(results)}
"""
summary_response = llm_client.one_chat(summary_prompt)
results.append(f"总体市场分析总结：\n{summary_response}")

# 将结果保存到analysis_result变量
analysis_result = "\n\n".join(results)