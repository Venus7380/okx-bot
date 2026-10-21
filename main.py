import time
import json
import ccxt
from openai import OpenAI
import os

API_KEY = os.getenv("OKX_API_KEY", "")
SECRET_KEY = os.getenv("OKX_SECRET_KEY", "")
PASSPHRASE = os.getenv("OKX_PASSPHRASE", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

COINS = ['XRP/USDT', 'AAVE/USDT', 'PEPE/USDT', 'DOGE/USDT', 'SOL/USDT', 'PENGU/USDT', 'SUI/USDT', 'STRK/USDT', 'ACT/USDT', 'ADA/USDT']

def run_trading_bot():
    print("🤖 Bulut Kripto Botu Başlatıldı...")
    try:
        exchange = ccxt.okx({
            'apiKey': API_KEY,
            'secret': SECRET_KEY,
            'password': PASSPHRASE,
            'options': {'defaultType': 'spot'}
        })
        client = OpenAI(api_key=OPENAI_KEY)
    except Exception as e:
        print(f"Bağlantı Hatası: {str(e)}")
        return

    while True:
        print("\n--- Yeni Tarama Döngüsü Başlıyor (15dk) ---")
        for symbol in COINS:
            try:
                print(f"Analiz ediliyor: {symbol}")
                ticker = exchange.fetch_ticker(symbol)
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=20)
                
                veri = {
                    "symbol": symbol,
                    "fiyat": ticker['last'],
                    "degisim": ticker['percentage'],
                    "mumlari": ohlcv
                }

                prompt = f"Sen profesyonel bir kripto trader'ısın. Şu verileri incele ve sadece JSON formatında yanıt ver: {json.dumps(veri)}. Yanıt formatı: {{\"action\": \"BUY\" (veya \"SELL\" veya \"HOLD\"), \"reason\": \"kısa gerekçe\"}}"
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                
                cevap = json.loads(response.choices[0].message.content)
                aksiyon = cevap.get("action")
                gerekce = cevap.get("reason")
                print(f"🎯 {symbol} -> Karar: {aksiyon} | Sebep: {gerekce}")

                bakiye = exchange.fetch_balance()
                usdt_bakiyesi = bakiye['free'].get('USDT', 0)
                base_currency = symbol.split('/')[0]
                base_bakiyesi = bakiye['free'].get(base_currency, 0)

                if aksiyon == "BUY":
                    if usdt_bakiyesi > 10:
                        harcanacak = usdt_bakiyesi * 0.05
                        miktar = harcanacak / ticker['last']
                        exchange.create_market_buy_order(symbol, miktar)
                        print(f"✅ {symbol} için BAŞARIYLA ALIM YAPILDI: {miktar}")
                    else:
                        print(f"⚠️ {symbol} alımı için yeterli USDT yok.")

                elif aksiyon == "SELL":
                    if base_bakiyesi > 0:
                        exchange.create_market_sell_order(symbol, base_bakiyesi)
                        print(f"✅ {symbol} için BAŞARIYLA SATIM YAPILDI: {base_bakiyesi}")
                    else:
                        print(f"⚠️ Satılacak {base_currency} bakiyesi yok.")

            except Exception as e:
                print(f"Hata oluştu ({symbol}): {str(e)}")
            
            time.sleep(5)

        print("⏳ Döngü tamamlandı, sonraki tarama 15 dakika sonra...")
        time.sleep(900)

if __name__ == '__main__':
    run_trading_bot()
