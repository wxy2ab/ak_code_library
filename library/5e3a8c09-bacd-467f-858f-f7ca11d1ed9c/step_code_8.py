import akshare as ak
from datetime import datetime
import pandas as pd

# 设置参数
symbol = "TK0"  # TK0 代表30年期国债期货连续合约
start_date = "20240101"  # 从2024年1月1日开始
end_date = datetime.now().strftime("%Y%m%d")  # 到当前日期

try:
    # 首先尝试使用futures_zh_daily_sina函数获取数据
    tk_data = ak.futures_zh_daily_sina(symbol=symbol)
    
    if tk_data.empty:
        # 如果futures_zh_daily_sina无法获取数据，尝试使用futures_main_sina
        tk_data = ak.futures_main_sina(symbol=symbol, start_date=start_date, end_date=end_date)
    
    if not tk_data.empty:
        # 过滤日期范围
        tk_data['date'] = pd.to_datetime(tk_data['date'])
        tk_data = tk_data[(tk_data['date'] >= start_date) & (tk_data['date'] <= end_date)]
        
        # 重置索引
        tk_data = tk_data.reset_index(drop=True)
    
    if tk_data.empty:
        print(f"未找到 {symbol} 在指定日期范围内的数据。")
    else:
        print(tk_data)
except Exception as e:
    print(f"获取数据时发生错误: {e}")
    tk_data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume', 'hold', 'settle'])

# 确保tk_data变量存在并且有列
if 'tk_data' not in locals() or tk_data.empty:
    tk_data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume', 'hold', 'settle'])

print(tk_data)