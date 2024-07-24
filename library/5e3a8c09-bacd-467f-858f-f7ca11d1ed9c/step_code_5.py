import akshare as ak
from datetime import datetime

# 设置参数
symbol = "TS0"  # TS0 代表2年期国债期货连续合约
start_date = "20240101"  # 从2024年1月1日开始
end_date = datetime.now().strftime("%Y%m%d")  # 到当前日期

# 使用futures_main_sina函数获取数据
ts_data = ak.futures_main_sina(symbol=symbol, start_date=start_date, end_date=end_date)

# 直接打印获取的数据，不做任何处理
print(ts_data)