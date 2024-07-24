import akshare as ak

# 获取IH主力连续合约数据
symbol = "IH0"  # IH0 代表中证50指数期货连续合约
start_date = "20240101"  # 从2024年1月1日开始
end_date = "20240403"  # 到当前日期

# 使用futures_main_sina函数获取数据
ih_data = ak.futures_main_sina(symbol=symbol, start_date=start_date, end_date=end_date)

# 直接返回获取的数据,不做任何处理
print(ih_data)