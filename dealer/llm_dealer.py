import json
import pandas as pd
from typing import Tuple, Literal
import logging
import re

from dealer.futures_provider import MainContractProvider

class LLMDealer:
    def __init__(self, llm_client, symbol: str, data_provider: MainContractProvider,
                 max_daily_bars: int = 30, max_hourly_bars: int = 24, max_minute_bars: int = 60):
        """
        初始化 LLMDealer 类
        
        :param llm_client: LLM API 客户端
        :param symbol: 交易的合约符号
        :param data_provider: MainContractProvider 实例
        :param max_daily_bars: 保留的最大日线历史数据天数
        :param max_hourly_bars: 保留的最大小时线历史数据条数
        :param max_minute_bars: 保留的最大分钟线历史数据条数
        """
        self.llm_client = llm_client
        self.symbol = symbol
        self.data_provider = data_provider
        self.max_daily_bars = max_daily_bars
        self.max_hourly_bars = max_hourly_bars
        self.max_minute_bars = max_minute_bars
        
        self.daily_history = self._initialize_history('D')
        self.hourly_history = self._initialize_history('60')
        self.minute_history = self._initialize_history('1')
        self.today_minute_bars = []
        self.last_msg = ""
        self.position = 0  # 当前持仓量，正数表示多头，负数表示空头

    def _initialize_history(self, period: Literal['1', '5', '15', '30', '60', 'D']) -> pd.DataFrame:
        """初始化历史数据，并确保日期列的一致性"""
        df = self.data_provider.get_bar_data(self.symbol, period)
        if period == 'D':
            df = self._standardize_daily_data(df)
        return self._limit_history(df, period)

    def _standardize_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化日线数据，使其与分钟数据格式一致"""
        df['datetime'] = pd.to_datetime(df['date'])
        df = df.drop(columns=['date'])
        return df

    def _limit_history(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """根据时间周期限制历史数据的长度"""
        if period == 'D':
            return df.tail(self.max_daily_bars)
        elif period == '60':
            return df.tail(self.max_hourly_bars)
        else:
            return df.tail(self.max_minute_bars)

    def _update_histories_old(self, bar: pd.Series):
        """更新历史数据"""
        # 更新分钟数据
        self.minute_history = self.minute_history.append(bar, ignore_index=True).tail(self.max_minute_bars)
        
        # 更新今日分钟数据
        if not self.today_minute_bars or bar['datetime'].date() > self.today_minute_bars[-1]['datetime'].date():
            self.today_minute_bars = [bar]
        else:
            self.today_minute_bars.append(bar)
        
        # 更新小时数据
        if bar['datetime'].minute == 0:
            self.hourly_history = self.hourly_history.append(bar, ignore_index=True).tail(self.max_hourly_bars)
        
        # 更新日线数据
        if bar['datetime'].hour == 15 and bar['datetime'].minute == 0:
            daily_bar = bar.copy()
            daily_bar['datetime'] = daily_bar['datetime'].date()
            self.daily_history = self.daily_history.append(daily_bar, ignore_index=True).tail(self.max_daily_bars)

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

    def _prepare_llm_input(self, bar: pd.Series, news: str) -> str:
        """准备发送给 LLM 的输入数据"""
        formatted_history = self._format_history()
        
        input_template = f"""
        上一次的消息: {self.last_msg}
        当前 bar index: {self._get_today_bar_index(bar['datetime'])}

        日线历史 (最近 {self.max_daily_bars} 天):
        {formatted_history['daily']}

        小时线历史 (最近 {self.max_hourly_bars} 小时):
        {formatted_history['hourly']}

        分钟线历史 (最近 {self.max_minute_bars} 分钟):
        {formatted_history['minute']}

        今日分钟线:
        {formatted_history['today_minute']}

        当前 bar 数据:
        时间: {bar['datetime'].strftime('%Y-%m-%d %H:%M')}
        开盘: {bar['open']:.2f}
        最高: {bar['high']:.2f}
        最低: {bar['low']:.2f}
        收盘: {bar['close']:.2f}
        成交量: {bar['volume']}
        持仓量: {bar['hold']}

        最新新闻:
        {news}

        当前持仓: {self.position}

        请根据以上信息，给出交易指令（buy/sell/short/cover）或不交易（hold），并提供下一次需要的消息。
        请以JSON格式输出，包含以下字段：
        - trade_instruction: 交易指令（字符串，可选值：buy, sell, short, cover, hold）
        - next_message: 下一次需要的消息（字符串）

        请确保输出的JSON格式正确，并用```json 和 ``` 包裹。
        """
        return input_template

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

    def _execute_trade(self, trade_instruction: str):
        """执行交易指令"""
        if trade_instruction == "buy":
            self.position += 1
        elif trade_instruction == "sell":
            self.position -= 1
        elif trade_instruction == "short":
            self.position -= 1
        elif trade_instruction == "cover":
            self.position += 1

    def _get_today_bar_index(self, timestamp: pd.Timestamp) -> int:
        """
        计算当前的 bar index，基于今日的分钟 bar 数量
        """
        today_bars = [bar for bar in self.today_minute_bars if bar['datetime'].date() == timestamp.date()]
        return len(today_bars) - 1  # 索引从0开始，所以减1

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

    def _update_histories(self, bar: pd.Series):
        """更新历史数据"""
        # 更新分钟数据
        self.minute_history = pd.concat([self.minute_history, bar.to_frame().T], ignore_index=True).tail(self.max_minute_bars)
        
        # 更新今日分钟数据
        if not self.today_minute_bars or bar['datetime'].date() > self.today_minute_bars[-1]['datetime'].date():
            self.today_minute_bars = [bar]
        elif self._is_trading_time(bar['datetime']):
            self.today_minute_bars.append(bar)
        
        # 更新小时数据
        if bar['datetime'].minute == 0 and self._is_trading_time(bar['datetime']):
            self.hourly_history = pd.concat([self.hourly_history, bar.to_frame().T], ignore_index=True).tail(self.max_hourly_bars)
        
        # 更新日线数据
        if bar['datetime'].hour == 15 and bar['datetime'].minute == 0:
            daily_bar = bar.copy()
            daily_bar['datetime'] = daily_bar['datetime'].date()
            self.daily_history = pd.concat([self.daily_history, daily_bar.to_frame().T], ignore_index=True).tail(self.max_daily_bars)

    def _log_bar_info(self, bar: pd.Series, news: str, trade_instruction: str):
        """记录每个 bar 的信息"""
        log_msg = f"""
        时间: {bar['datetime']}, Bar Index: {self._get_today_bar_index(bar['datetime'])}
        价格: 开 {bar['open']}, 高 {bar['high']}, 低 {bar['low']}, 收 {bar['close']}
        成交量: {bar['volume']}, 持仓量: {bar['hold']}
        新闻: {news[:100]}...  # 截取前100个字符
        交易指令: {trade_instruction}
        当前持仓: {self.position}
        """
        logging.info(log_msg)