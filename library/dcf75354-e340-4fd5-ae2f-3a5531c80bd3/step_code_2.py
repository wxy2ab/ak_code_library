import pandas as pd
import re

# 准备输入数据
input_data = cosco_daily_data_2024[['date', 'close']].set_index('date')

# 定义数据处理函数
def data_processor(data):
    return data.asfreq('D').fillna(method='ffill').iloc[-30:]  # 使用最近30天的数据

# 定义响应处理函数
def response_processor(response, num_of_predict):
    # 使用正则表达式提取数字
    numbers = re.findall(r'\d+\.\d+', response)
    predictions = [float(num) for num in numbers[-num_of_predict:]]
    return pd.Series(predictions, name='close', index=pd.date_range(start=input_data.index[-1] + pd.Timedelta(days=1), periods=num_of_predict))

# 使用llm_client进行预测
predictions = llm_client.predict(input_data, num_of_predict=5, data_processor=data_processor, response_processor=response_processor)