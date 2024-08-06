import time
import pandas as pd
from typing import List, Tuple
from datetime import datetime, timedelta

from tqdm import tqdm
from dealer.futures_provider import MainContractProvider
from dealer.llm_dealer import LLMDealer

class Backtester:
    def __init__(self, symbol: str, start_date: str, end_date: str, llm_client, data_provider: MainContractProvider):
        self.symbol = symbol
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.llm_client = llm_client
        self.data_provider = data_provider
        
        self.trades: List[Tuple[str, float, datetime]] = []  # (action, price, timestamp)
        self.open_trades = 0
        self.close_trades = 0
        self.profit_loss = 0

    def run_backtest(self):
        total_days = (self.end_date - self.start_date).days + 1
        current_date = self.start_date
        start_time = time.time()

        with tqdm(total=total_days, desc="Overall Progress") as pbar:
            while current_date <= self.end_date:
                print(f"\nProcessing date: {current_date.strftime('%Y-%m-%d')}")
                
                # 初始化当天的 LLMDealer
                dealer = LLMDealer(self.llm_client, self.symbol, self.data_provider, backtest_date=current_date.strftime('%Y-%m-%d'))
                
                # 获取当天的分钟线数据
                minute_data = self.data_provider.get_bar_data(self.symbol, '1', current_date.strftime('%Y-%m-%d'))
                
                # 按时间顺序处理每个分钟的数据
                for i, (_, bar) in enumerate(minute_data.iterrows(), 1):
                    trade_instruction, _ = dealer.process_bar(bar)
                    self._record_trade(trade_instruction, bar['close'], bar['datetime'])
                    
                    # 每处理50个bar显示一次进度
                    if i % 50 == 0:
                        print(f"Processed {i}/{len(minute_data)} bars for {current_date.strftime('%Y-%m-%d')}")
                
                current_date += timedelta(days=1)
                pbar.update(1)
                
                # 估计剩余时间
                elapsed_time = time.time() - start_time
                days_processed = (current_date - self.start_date).days
                if days_processed > 0:
                    avg_time_per_day = elapsed_time / days_processed
                    remaining_days = total_days - days_processed
                    estimated_time_left = remaining_days * avg_time_per_day
                    print(f"Estimated time remaining: {timedelta(seconds=int(estimated_time_left))}")

        self._calculate_performance()
        print("\nBacktest completed!")

    def _record_trade(self, instruction: str, price: float, timestamp: datetime):
        if instruction in ['buy', 'short']:
            self.trades.append((instruction, price, timestamp))
            self.open_trades += 1
        elif instruction in ['sell', 'cover']:
            if self.trades:
                last_trade = self.trades[-1]
                if (instruction == 'sell' and last_trade[0] == 'buy') or (instruction == 'cover' and last_trade[0] == 'short'):
                    pl = (price - last_trade[1]) * (1 if last_trade[0] == 'buy' else -1)
                    self.profit_loss += pl
                    self.trades.append((instruction, price, timestamp))
                    self.close_trades += 1

    def _calculate_performance(self):
        print(f"回测结果 ({self.start_date.strftime('%Y-%m-%d')} 到 {self.end_date.strftime('%Y-%m-%d')}):")
        print(f"开仓次数: {self.open_trades}")
        print(f"平仓次数: {self.close_trades}")
        print(f"最终盈亏点数: {self.profit_loss:.2f}")
        
        if self.open_trades > 0:
            win_rate = (self.close_trades / self.open_trades) * 100
            print(f"胜率: {win_rate:.2f}%")
        
        if self.close_trades > 0:
            avg_profit = self.profit_loss / self.close_trades
            print(f"平均每笔交易盈亏: {avg_profit:.2f}")

    def get_trade_history(self) -> pd.DataFrame:
        return pd.DataFrame(self.trades, columns=['Action', 'Price', 'Timestamp'])

# 使用示例
if __name__ == "__main__":
    symbol = "SC"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    data_provider = MainContractProvider()
    llm_client = None  # 替换为实际的 LLM 客户端
    
    backtester = Backtester(symbol, start_date, end_date, llm_client, data_provider)
    backtester.run_backtest()
    
    # 获取详细的交易历史
    trade_history = backtester.get_trade_history()
    print(trade_history)