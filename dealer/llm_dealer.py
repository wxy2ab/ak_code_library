import json
import time
import numpy as np
import pandas as pd
from ta import add_all_ta_features
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands, AverageTrueRange
from typing import Tuple, Literal, Optional, Union
import logging
import re
from datetime import datetime, timedelta, time as dt_time

from dealer.futures_provider import MainContractProvider

class LLMDealer:
    def __init__(self, llm_client, symbol: str, data_provider: MainContractProvider,
                 max_daily_bars: int = 30, max_hourly_bars: int = 12, max_minute_bars: int = 60,
                 backtest_date: Optional[str] = None, compact_mode: bool = False
                 ):
        self.llm_client = llm_client
        self.symbol = symbol
        self.data_provider = data_provider
        self.max_daily_bars = max_daily_bars
        self.max_hourly_bars = max_hourly_bars
        self.max_minute_bars = max_minute_bars
        self.compact_mode = compact_mode
        self.backtest_date = backtest_date or datetime.now().strftime('%Y-%m-%d')
        
        self.daily_history = self._initialize_history('D')
        self.hourly_history = self._initialize_history('60')  # 改为 '1H'
        self.minute_history = self._initialize_history('1')
        self.today_minute_bars = pd.DataFrame()
        self.last_msg = ""
        self.position = 0  # 当前持仓量，正数表示多头，负数表示空头
        self.current_date = None
        self.last_trade_date = None  # 添加这个属性
        
        self.trading_hours = [
            (dt_time(9, 0), dt_time(11, 30)),
            (dt_time(13, 0), dt_time(15, 0)),
            (dt_time(21, 0), dt_time(23, 59)),
            (dt_time(0, 0), dt_time(2, 30))
        ]

    def _is_trading_time(self, dt: datetime) -> bool:
        t = dt.time()
        for start, end in self.trading_hours:
            if start <= t <= end:
                return True
        return False

    def _filter_trading_data(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df['datetime'].apply(self._is_trading_time)]

    def _get_today_data(self, date: datetime.date) -> pd.DataFrame:
        minute_data = self.data_provider.get_bar_data(self.symbol, '1', date.strftime('%Y-%m-%d'))
        minute_data['datetime'] = pd.to_datetime(minute_data['datetime'])
        return self._filter_trading_data(minute_data)
    
    def _validate_and_prepare_data(self, df: pd.DataFrame, date: str) -> pd.DataFrame:
        original_len = len(df)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df[df['datetime'].dt.date == pd.to_datetime(date).date()]
        df = self._filter_trading_data(df)
        
        logging.info(f"Bars for date {date}: Original: {original_len}, After filtering: {len(df)}")
        
        if len(df) > self.max_minute_bars:
            logging.warning(f"Unusually high number of bars ({len(df)}) for date {date}. Trimming to {self.max_minute_bars} bars.")
            df = df.tail(self.max_minute_bars)
        
        return df

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理数据，处理空值和异常值"""
        # 将所有列转换为数值类型，非数值替换为 NaN
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 使用前向填充方法填充 NaN 值
        df = df.fillna(method='ffill')

        # 如果仍有 NaN 值（比如在数据开始处），则使用后向填充
        df = df.fillna(method='bfill')

        # 确保没有负值
        for col in numeric_columns:
            df[col] = df[col].clip(lower=0)

        return df

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 5:  # 降低最小数据点要求
            return df
        
        try:
            df['sma_10'] = df['close'].rolling(window=min(10, len(df))).mean()
            df['ema_20'] = df['close'].ewm(span=min(20, len(df)), adjust=False).mean()
            df['rsi'] = RSIIndicator(close=df['close'], window=min(14, len(df))).rsi()
            
            macd = MACD(close=df['close'], window_slow=min(26, len(df)), window_fast=min(12, len(df)), window_sign=min(9, len(df)))
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            
            bollinger = BollingerBands(close=df['close'], window=min(20, len(df)), window_dev=2)
            df['bollinger_high'] = bollinger.bollinger_hband()
            df['bollinger_mid'] = bollinger.bollinger_mavg()
            df['bollinger_low'] = bollinger.bollinger_lband()
            
            df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=min(14, len(df))).average_true_range()
        except Exception as e:
            logging.error(f"Error calculating indicators: {str(e)}")
        
        return df

    def _format_indicators(self, indicators: pd.Series) -> str:
        if self.compact_mode:
            return f"""
            SMA10: {indicators.get('sma_10', 'N/A'):.2f}
            EMA20: {indicators.get('ema_20', 'N/A'):.2f}
            RSI: {indicators.get('rsi', 'N/A'):.2f}
            MACD: {indicators.get('macd', 'N/A'):.2f}
            BB高: {indicators.get('bollinger_high', 'N/A'):.2f}
            BB低: {indicators.get('bollinger_low', 'N/A'):.2f}
            """
        else:
            return f"""
            10周期简单移动平均线 (SMA): {indicators.get('sma_10', 'N/A'):.2f}
            20周期指数移动平均线 (EMA): {indicators.get('ema_20', 'N/A'):.2f}
            相对强弱指标 (RSI): {indicators.get('rsi', 'N/A'):.2f}
            MACD: {indicators.get('macd', 'N/A'):.2f}
            MACD信号线: {indicators.get('macd_signal', 'N/A'):.2f}
            平均真实范围 (ATR): {indicators.get('atr', 'N/A'):.2f}
            布林带上轨: {indicators.get('bollinger_high', 'N/A'):.2f}
            布林带中轨: {indicators.get('bollinger_mid', 'N/A'):.2f}
            布林带下轨: {indicators.get('bollinger_low', 'N/A'):.2f}
            """
        
    def _initialize_history(self, period: Literal['1', '5', '15', '30', '60', 'D']) -> pd.DataFrame:
        try:
            df = self.data_provider.get_bar_data(self.symbol, period, self.backtest_date)
            
            # 检查数据是否为空
            if df.empty:
                raise ValueError(f"No data returned for period {period}")
            
            # 统一列名
            if 'date' in df.columns:
                df = df.rename(columns={'date': 'datetime'})
            
            # 确保 'datetime' 列是 datetime 类型
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            # 选择需要的列
            columns_to_keep = ['datetime', 'open', 'close', 'high', 'low', 'volume', 'hold']
            df = df[columns_to_keep]
            
            return self._limit_history(df, period)
        except Exception as e:
            logging.error(f"Error initializing history for period {period}: {str(e)}")
            # 返回一个空的 DataFrame，包含所有必要的列
            return pd.DataFrame(columns=['datetime', 'open', 'close', 'high', 'low', 'volume', 'hold'])

    def _limit_history(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """根据时间周期限制历史数据的长度"""
        if df.empty:
            return df
        if period == 'D':
            return df.tail(self.max_daily_bars)
        elif period == '60':
            return df.tail(self.max_hourly_bars)
        else:
            return df.tail(self.max_minute_bars)

    def _update_histories(self, bar: pd.Series):
        """更新历史数据"""
        # 更新分钟数据
        self.minute_history = pd.concat([self.minute_history, bar.to_frame().T], ignore_index=True).tail(self.max_minute_bars)
        
        # 更新小时数据
        if bar['datetime'].minute == 0:
            self.hourly_history = pd.concat([self.hourly_history, bar.to_frame().T], ignore_index=True).tail(self.max_hourly_bars)
        
        # 更新日线数据
        if bar['datetime'].hour == 15 and bar['datetime'].minute == 0:
            daily_bar = bar.copy()
            daily_bar['datetime'] = daily_bar['datetime'].date()
            self.daily_history = pd.concat([self.daily_history, daily_bar.to_frame().T], ignore_index=True).tail(self.max_daily_bars)

    def _format_history(self) -> dict:
        """格式化历史数据，确保所有数据都被包含，并且格式一致"""
        
        def format_dataframe(df: pd.DataFrame, max_rows: int = None) -> str:
            if max_rows and len(df) > max_rows:
                df = df.tail(max_rows)  # 只保留最后 max_rows 行
            
            df_reset = df.reset_index(drop=True)
            formatted = df_reset.to_string(index=True, index_names=False, 
                                            formatters={
                                                'datetime': lambda x: x.strftime('%Y-%m-%d %H:%M') if isinstance(x, pd.Timestamp) else str(x),
                                                'open': '{:.2f}'.format,
                                                'high': '{:.2f}'.format,
                                                'low': '{:.2f}'.format,
                                                'close': '{:.2f}'.format
                                            })
            return formatted

        return {
            'daily': format_dataframe(self.daily_history, self.max_daily_bars),
            'hourly': format_dataframe(self.hourly_history, self.max_hourly_bars),
            'minute': format_dataframe(self.minute_history, self.max_minute_bars),
            'today_minute': format_dataframe(pd.DataFrame(self.today_minute_bars))
        }

    def _compress_history(self, df: pd.DataFrame, period: str) -> str:
        if df.empty:
            return "No data available"
        
        df = df.tail(self.max_daily_bars if period == 'D' else self.max_hourly_bars if period == 'H' else self.max_minute_bars)
        
        summary = []
        for _, row in df.iterrows():
            if self.compact_mode:
                summary.append(f"{row['datetime'].strftime('%Y-%m-%d %H:%M' if period != 'D' else '%Y-%m-%d')}: "
                               f"C:{row['close']:.2f} V:{row['volume']}")
            else:
                summary.append(f"{row['datetime'].strftime('%Y-%m-%d %H:%M' if period != 'D' else '%Y-%m-%d')}: "
                               f"O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f} V:{row['volume']}")
        
        return "\n".join(summary)
    
    def _prepare_llm_input(self, bar: pd.Series, news: str) -> str:
        if self.today_minute_bars.empty:
            return "Insufficient data for LLM input"
        
        today_data = self._calculate_indicators(self.today_minute_bars)
        latest_indicators = today_data.iloc[-1]
        
        # Compress historical data
        daily_summary = self._compress_history(self.daily_history, 'D')
        hourly_summary = self._compress_history(self.hourly_history, 'H')
        minute_summary = self._compress_history(self.today_minute_bars, 'T')
        
        open_interest = bar.get('hold', 'N/A')
    
        input_template = f"""
        上一次的消息: {self.last_msg}
        当前 bar index: {len(self.today_minute_bars) - 1}

        日线历史摘要 (最近 {self.max_daily_bars} 天):
        {daily_summary}

        小时线历史摘要 (最近 {self.max_hourly_bars} 小时):
        {hourly_summary}

        今日分钟线摘要 (最近 {self.max_minute_bars} 分钟):
        {minute_summary}

        当前 bar 数据:
        时间: {bar['datetime'].strftime('%Y-%m-%d %H:%M')}
        开盘: {bar['open']:.2f}
        最高: {bar['high']:.2f}
        最低: {bar['low']:.2f}
        收盘: {bar['close']:.2f}
        成交量: {bar['volume']}
        持仓量: {open_interest}

        技术指标:
        {self._format_indicators(latest_indicators)}

        最新新闻:
        {news[:200]}...  # 限制新闻长度

        当前持仓: {self.position}

        请注意：
        1. 日内仓位需要在每天15:00之前平仓。
        2. 当前时间为 {bar['datetime'].strftime('%H:%M')}，请根据时间决定是否需要平仓。

        请根据以上信息，给出交易指令（buy/sell/short/cover）或不交易（hold），并提供下一次需要的消息。
        请以JSON格式输出，包含以下字段：
        - trade_instruction: 交易指令（字符串，可选值：buy, sell, short, cover, hold）
        - next_message: 下一次需要的消息（字符串）

        请确保输出的JSON格式正确，并用```json 和 ``` 包裹。
        """
        return input_template

    def _format_history(self) -> dict:
        """格式化历史数据"""
        return {
            'daily': self.daily_history.to_string(index=False) if not self.daily_history.empty else "No daily data available",
            'hourly': self.hourly_history.to_string(index=False) if not self.hourly_history.empty else "No hourly data available",
        }

    def _parse_llm_output(self, llm_response: str) -> Tuple[str, str]:
        """解析 LLM 的 JSON 输出"""
        try:
            # 提取 JSON 内容
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in the response")
            
            json_str = json_match.group(1)
            data = json.loads(json_str)
            
            # 验证 JSON 结构
            if 'trade_instruction' not in data or 'next_message' not in data:
                raise ValueError("Invalid JSON structure")
            
            trade_instruction = data['trade_instruction']
            next_msg = data['next_message']
            
            # 验证 trade_instruction
            if trade_instruction not in ['buy', 'sell', 'short', 'cover', 'hold']:
                raise ValueError(f"Invalid trade instruction: {trade_instruction}")
            
            return trade_instruction, next_msg
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error: {e}")
            return "hold", ""
        except ValueError as e:
            logging.error(f"Validation error: {e}")
            return "hold", ""
        except Exception as e:
            logging.error(f"Unexpected error while parsing LLM output: {e}")
            return "hold", ""

    def _execute_trade(self, trade_instruction: str, bar: pd.Series):
        """执行交易指令，并在必要时强制平仓"""
        current_date = bar['datetime'].date()
        current_time = bar['datetime'].time()

        # 如果是新的交易日，重置仓位
        if self.last_trade_date != current_date:
            self.position = 0
            self.last_trade_date = current_date

        # 执行交易指令
        if trade_instruction == "buy":
            self.position += 1
        elif trade_instruction == "sell":
            self.position -= 1
        elif trade_instruction == "short":
            self.position -= 1
        elif trade_instruction == "cover":
            self.position += 1

        # 强制平仓逻辑
        closing_time = dt_time(14, 55)
        if current_time >= closing_time:  # 在14:55或之后
            if self.position > 0:
                logging.info(f"强制平多仓：{self.position}")
                self.position = 0
            elif self.position < 0:
                logging.info(f"强制平空仓：{self.position}")
                self.position = 0

    def _get_today_bar_index(self, timestamp: pd.Timestamp) -> int:
        """
        计算当前的 bar index，基于今日的分钟 bar 数量
        """
        if self.today_minute_bars.empty:
            return 0
        
        try:
            # 确保 datetime 列是 datetime 类型
            self.today_minute_bars['datetime'] = pd.to_datetime(self.today_minute_bars['datetime'])
            today_bars = self.today_minute_bars[self.today_minute_bars['datetime'].dt.date == timestamp.date()]
            return len(today_bars)
        except Exception as e:
            logging.error(f"Error in _get_today_bar_index: {str(e)}", exc_info=True)
            return 0

    def _is_trading_time(self, timestamp: pd.Timestamp) -> bool:
        """
        判断给定时间是否在交易时间内
        """
        # 定义交易时间段（根据实际情况调整）
        trading_sessions = [
            ((9, 0), (11, 30)),   # 上午交易时段
            ((13, 0), (15, 0)),   # 下午交易时段
            ((21, 0), (23, 59)),  # 夜盘交易时段开始
            ((0, 0), (2, 30))     # 夜盘交易时段结束（跨天）
        ]
        
        time = timestamp.time()
        for start, end in trading_sessions:
            if start <= (time.hour, time.minute) <= end:
                return True
        return False

    def _log_bar_info(self, bar: Union[pd.Series, dict], news: str, trade_instruction: str):
        """记录每个 bar 的信息"""
        try:
            # 打印 bar 的类型和内容，以便调试
            logging.debug(f"Bar type: {type(bar)}")
            logging.debug(f"Bar content: {bar}")

            # 如果 bar 是字典，将其转换为 pd.Series
            if isinstance(bar, dict):
                bar = pd.Series(bar)
            elif isinstance(bar, str):
                # 如果 bar 是字符串，尝试解析它
                try:
                    bar = pd.Series(eval(bar))
                except:
                    logging.error(f"Unable to parse bar string: {bar}")
                    return
            elif not isinstance(bar, pd.Series):
                raise TypeError(f"bar must be a pandas Series or dict, but got {type(bar)}")

            # 使用 .get() 方法安全地访问 bar 的属性
            datetime = pd.to_datetime(bar.get('datetime', 'N/A'))
            open_price = bar.get('open', 'N/A')
            high_price = bar.get('high', 'N/A')
            low_price = bar.get('low', 'N/A')
            close_price = bar.get('close', 'N/A')
            volume = bar.get('volume', 'N/A')
            open_interest = bar.get('open_interest', bar.get('hold', 'N/A'))

            # 格式化价格，如果是数值的话
            format_price = lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x

            log_msg = f"""
            时间: {datetime}, Bar Index: {self._get_today_bar_index(datetime) if isinstance(datetime, pd.Timestamp) else 'N/A'}
            价格: 开 {format_price(open_price)}, 高 {format_price(high_price)}, 低 {format_price(low_price)}, 收 {format_price(close_price)}
            成交量: {volume}, 持仓量: {open_interest}
            新闻: {news[:100]}...  # 截取前100个字符
            交易指令: {trade_instruction}
            当前持仓: {self.position}
            """
            logging.info(log_msg)
        except Exception as e:
            logging.error(f"Error in _log_bar_info: {str(e)}", exc_info=True)
    
    def process_bar(self, bar: pd.Series, news: str = "") -> Tuple[str, str]:
        try:
            bar['datetime'] = pd.to_datetime(bar['datetime'])
            bar_date = bar['datetime'].date()

            if self.current_date != bar_date:
                self.current_date = bar_date
                self.today_minute_bars = self._get_today_data(bar_date)
                self.position = 0
                self.last_trade_date = bar_date

            if not self._is_trading_time(bar['datetime']):
                return "hold", ""

            # Update today_minute_bars only if it's a trading time
            self.today_minute_bars = pd.concat([self.today_minute_bars, bar.to_frame().T], ignore_index=True)

            llm_input = self._prepare_llm_input(bar, news)
            llm_response = self.llm_client.one_chat(llm_input)
            trade_instruction, next_msg = self._parse_llm_output(llm_response)
            self._execute_trade(trade_instruction, bar)
            self._log_bar_info(bar, news, trade_instruction)
            self.last_msg = next_msg
            return trade_instruction, next_msg
        except Exception as e:
            logging.error(f"Error processing bar: {str(e)}")
            return "hold", ""