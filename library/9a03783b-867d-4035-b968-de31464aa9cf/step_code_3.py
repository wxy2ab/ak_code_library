import akshare as ak
from datetime import datetime

cosco_news_data_2024 = ak.stock_news_em(symbol="601919")
cosco_news_data_2024 = cosco_news_data_2024[cosco_news_data_2024['发布时间'].apply(lambda x: x.startswith('2024'))]