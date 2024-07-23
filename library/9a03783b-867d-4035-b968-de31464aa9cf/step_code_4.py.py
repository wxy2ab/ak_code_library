import pandas as pd
from datetime import datetime, timedelta

# 初始化 LLMFactor
llm_factor = llm_factory.class_instantiation("LLMFactor")

# 准备数据
cosco_daily_data_2024['日期'] = pd.to_datetime(cosco_daily_data_2024['日期'])
shanghai_index_data_2024['date'] = pd.to_datetime(shanghai_index_data_2024['date'])

# 获取最新日期
latest_date = cosco_daily_data_2024['日期'].max()

# 准备新闻数据
news_data = cosco_news_data_2024[['发布时间', '新闻标题']].rename(columns={'发布时间': 'date', '新闻标题': 'headline'})
news_data['date'] = pd.to_datetime(news_data['date'])
news_data = news_data.sort_values('date', ascending=False).head(10).to_dict('records')

# 准备股票数据
cosco_data = cosco_daily_data_2024.reset_index().rename(columns={
    '日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'
})
cosco_data['date'] = pd.to_datetime(cosco_data['date'])
cosco_data = cosco_data.set_index('date')

shanghai_data = shanghai_index_data_2024.set_index('date')[['open', 'close', 'high', 'low', 'volume']]

# 分析并预测
target_date = latest_date + timedelta(days=1)
result = llm_factor.analyze("中远海控", "上证指数", True, news_data, cosco_data.reset_index(), shanghai_data.reset_index(), target_date)

# 使用 llm_client 进行预测
cosco_predictions = llm_client.predict_with_news(
    cosco_data.reset_index(),
    news_data,
    num_of_predict=5,
    stock_symbol="中远海控",
    interval="天"
)