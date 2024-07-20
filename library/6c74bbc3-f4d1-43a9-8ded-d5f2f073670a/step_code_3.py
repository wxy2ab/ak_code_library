import pandas as pd
from datetime import datetime, timedelta

# 获取最新的交易日期
latest_date = pd.to_datetime(cosco_daily_data_2024['日期']).max()

# 获取最近5天的股价数据
recent_prices = cosco_daily_data_2024.sort_values('日期', ascending=False).head(5)['收盘'].tolist()[::-1]

# 获取最近5条新闻
recent_news = cosco_news_data.sort_values('发布时间', ascending=False).head(5)

# 准备新闻数据
news_data = [
    {
        'date': row['发布时间'],
        'headline': row['新闻标题']
    }
    for _, row in recent_news.iterrows()
]

# 使用llm_client预测未来5个交易日的市场表现
predictions = llm_client.predict_with_news(
    stock_prices=recent_prices,
    news_data=news_data,
    num_of_predict=5,
    stock_symbol=symbol,
    interval="天"
)