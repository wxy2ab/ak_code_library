


from dealer.backtester import Backtester
from dealer.futures_provider import MainContractProvider


def test():
    symbol = "SC"
    start_date = "2024-06-03"
    end_date = "2024-06-8"
    
    data_provider = MainContractProvider()
    from core.llms.llm_factory import LLMFactory
    factory = LLMFactory()

    llm_client = factory.get_instance("MiniMaxClient")
    
    backtester = Backtester(symbol, start_date, end_date, llm_client, data_provider,compact_mode=True)
    backtester.run_backtest()
    
    # 获取详细的交易历史
    trade_history = backtester.get_trade_history()
    print(trade_history)

def test1():
    data_provider = MainContractProvider()
    df=data_provider.get_bar_data("SC","D", "2024-06-01")

    print(df)

def main():
    test()

if __name__ == '__main__':
    main()