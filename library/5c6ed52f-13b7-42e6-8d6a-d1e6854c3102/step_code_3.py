import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import os
from collections import Counter

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 访问之前步骤的数据
research_reports = cosco_research_reports
company_info = cosco_company_info

# 分析研报评级
ratings = research_reports['东财评级'].value_counts()
plt.figure(figsize=(10, 6))
ratings.plot(kind='bar')
plt.title('中远海控研报评级分布')
plt.xlabel('评级')
plt.ylabel('数量')
file_name = f"output/{uuid.uuid4()}.png"
plt.savefig(file_name)
plt.close()

# 分析预测收益
plt.figure(figsize=(12, 6))
sns.boxplot(data=research_reports[['2023-盈利预测-收益', '2024-盈利预测-收益']])
plt.title('中远海控2023-2024年盈利预测')
plt.ylabel('预测收益')
file_name2 = f"output/{uuid.uuid4()}.png"
plt.savefig(file_name2)
plt.close()

# 分析研报内容
report_titles = research_reports['报告名称'].tolist()
llm_client = llm_factory.get_instance()
prompt = f"分析以下中远海控的研报标题，总结出主要的市场机会、市场竞争、前景展望、潜在风险和机遇：\n{', '.join(report_titles)}"
response = llm_client.one_chat(prompt)

# 准备返回值
results = []
results.append(f"![研报评级分布]({file_name})")
results.append(f"![盈利预测分布]({file_name2})")
results.append("主要发现：")
results.append(f"1. 研报评级分布：买入 {ratings.get('买入', 0)}，增持 {ratings.get('增持', 0)}，中性 {ratings.get('中性', 0)}")
results.append(f"2. 2023年平均预测收益：{research_reports['2023-盈利预测-收益'].mean():.2f}")
results.append(f"3. 2024年平均预测收益：{research_reports['2024-盈利预测-收益'].mean():.2f}")
results.append("4. LLM分析结果：")
results.append(response)

# 将结果保存到analysis_result变量
analysis_result = "\n".join(results)