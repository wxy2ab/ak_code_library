import akshare as ak
from datetime import datetime

current_date = datetime.now().strftime("%Y%m%d")
cosco_daily_data_2024 = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20240101", end_date=current_date, adjust="")