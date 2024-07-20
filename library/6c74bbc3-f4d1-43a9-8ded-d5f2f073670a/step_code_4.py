import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import os
from matplotlib import font_manager

# 设置中文字体
font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 处理历史数据
cosco_daily_data_2024['日期'] = pd.to_datetime(cosco_daily_data_2024['日期'])
historical_data = cosco_daily_data_2024.sort_values('日期')

# 处理预测数据
last_date = historical_data['日期'].iloc[-1]
prediction_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 6)]
prediction_prices = [p['price'] for p in predictions]
prediction_df = pd.DataFrame({'日期': prediction_dates, '预测收盘': prediction_prices})

# 绘图
plt.figure(figsize=(12, 6))
plt.plot(historical_data['日期'], historical_data['收盘'], label='历史收盘价')
plt.plot(prediction_df['日期'], prediction_df['预测收盘'], color='red', label='预测收盘价')
plt.title('中远海控(601919)股价历史数据与预测')
plt.xlabel('日期')
plt.ylabel('股价')
plt.legend()
plt.grid(True)

# 保存图表
file_name = f"output/{uuid.uuid4()}.png"
plt.savefig(file_name)
plt.close()

# 计算一些统计数据
last_price = historical_data['收盘'].iloc[-1]
predicted_change = (prediction_df['预测收盘'].iloc[-1] - last_price) / last_price * 100

# 准备返回值
results = []
results.append(f"![中远海控股价历史与预测分析]({file_name})")
results.append("主要发现：")
results.append(f"1. 最新收盘价: {last_price:.2f}元")
results.append(f"2. 5天后预测价: {prediction_df['预测收盘'].iloc[-1]:.2f}元")
results.append(f"3. 预测变动幅度: {predicted_change:.2f}%")
results.append(f"4. 历史最高价: {historical_data['最高'].max():.2f}元")
results.append(f"5. 历史最低价: {historical_data['最低'].min():.2f}元")
results.append(f"6. 平均成交量: {historical_data['成交量'].mean():.0f}股")

# 使用LLM API进行趋势分析
llm_client = llm_factory.get_instance()
trend_prompt = f"根据以下数据分析中远海控(601919)未来5天的股价趋势：最新收盘价{last_price:.2f}元，5天后预测价{prediction_df['预测收盘'].iloc[-1]:.2f}元，预测变动幅度{predicted_change:.2f}%。请给出简要分析。"
trend_analysis = llm_client.one_chat(trend_prompt)

results.append("7. LLM趋势分析:")
results.append(trend_analysis)

# 将结果保存到analysis_result变量
analysis_result = "\n".join(results)