import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import os
import platform

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 设置中文字体
if platform.system() == 'Linux':
    from matplotlib import font_manager
    font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']
elif platform.system() == 'Windows':
    plt.rcParams['font.sans-serif'] = ['msyh.ttc']
elif platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['/System/Library/Fonts/PingFang.ttc']

# 处理数据
cosco_daily_data_2024['日期'] = pd.to_datetime(cosco_daily_data_2024['日期'])
cosco_predictions['date'] = pd.to_datetime(cosco_predictions['date'])

# 绘制图表
plt.figure(figsize=(12, 6))
plt.plot(cosco_daily_data_2024['日期'], cosco_daily_data_2024['收盘'], label='历史数据')
plt.plot(cosco_predictions['date'], cosco_predictions['close'], color='red', label='预测数据')
plt.title('中远海控历史数据和预测数据')
plt.xlabel('日期')
plt.ylabel('收盘价')
plt.legend()
plt.grid(True)

# 生成唯一文件名并保存图表
filename = f'output/cosco_analysis_{uuid.uuid4()}.png'
plt.savefig(filename)
plt.close()

# 分析结果
last_historical = cosco_daily_data_2024['收盘'].iloc[-1]
last_predicted = cosco_predictions['close'].iloc[-1]
price_change = (last_predicted - last_historical) / last_historical * 100

analysis_result = f"""
分析结果：
1. 最新历史收盘价：{last_historical:.2f}
2. 最新预测收盘价：{last_predicted:.2f}
3. 预测价格变化：{price_change:.2f}%
4. 预测趋势：{'上涨' if price_change > 0 else '下跌'}
"""

# 生成Markdown格式的结果
markdown_result = f"""
![中远海控股价分析图]({filename})

{analysis_result}
"""

# 将结果赋值给变量而不是直接返回
cosco_analysis_result = markdown_result