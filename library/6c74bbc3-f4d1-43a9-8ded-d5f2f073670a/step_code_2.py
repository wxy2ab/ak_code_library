import akshare as ak
import datetime

# 获取当前日期
today = datetime.date.today()

# 获取2024年1月1日至今的日线数据
cosco_daily_data_2024 = ak.stock_zh_a_hist(symbol=symbol, start_date="20240101", end_date=today.strftime("%Y%m%d"), adjust="")

# 注意：这里我们不对数据结构做任何处理，保持API返回时的结构