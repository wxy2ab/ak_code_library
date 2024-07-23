import akshare as ak
import datetime

# 获取中远海控2024年的日线股票数据
# 中远海控的股票代码是 "601919.SH"

# 使用stock_zh_a_daily函数获取数据
# 获取今天的日期
today = datetime.date.today()

# 将日期转换成yyyyMMdd格式
end_date = today.strftime("%Y%m%d")

# 使用stock_zh_a_daily函数获取数据
cosco_daily_data_2024 = ak.stock_zh_a_daily(symbol=symbol, start_date="20240101", end_date=end_date)

# 直接打印返回的数据，不做任何处理
print(cosco_daily_data_2024)