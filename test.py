



def test():
    import akshare as ak
    from dealer.futures_provider import MainContractProvider
    from dealer.futures_provider import MainContractGetter
    from core.interpreter.data_summarizer import DataSummarizer
    data = MainContractProvider()
    
    df = data.get_futures_news(code="SC0")
    print(df)   
    #df = ak.futures_zh_minute_sina(symbol="Cu0",period="1")


def main():
    test()

if __name__ == '__main__':
    main()