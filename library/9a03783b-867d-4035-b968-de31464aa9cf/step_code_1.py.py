import akshare as ak
from datetime import datetime

current_date = datetime.now().strftime("%Y%m%d")
shanghai_index_data_2024 = ak.stock_zh_index_daily_em(symbol="sh000001", start_date="20240101", end_date=current_date)