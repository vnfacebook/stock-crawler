from src.crawlers.ssi import SSICrawler
from src.utils.logger import logger
import json

def test_ssi():
    crawler = SSICrawler()
    
    symbol = "FPT"
    
    logger.info("--- Testing SSI Realtime Price ---")
    realtime_data = crawler.fetch_realtime_price(symbol)
    if realtime_data:
        # SSI returns a lot of fields, let's print some key ones
        summary = {
            "Symbol": realtime_data.get("ss"),
            "Price": realtime_data.get("l"),
            "Change": realtime_data.get("c"),
            "Volume": realtime_data.get("v"),
            "High": realtime_data.get("h"),
            "Low": realtime_data.get("lo"),
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        # Uncomment to see full data
        # print(json.dumps(realtime_data, indent=2, ensure_ascii=False))
    else:
        logger.error("Failed to fetch data.")

    logger.info("--- Testing SSI Financial Info ---")
    finance_data = crawler.fetch_financial_info(symbol)
    if finance_data:
        print(json.dumps(finance_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_ssi()
