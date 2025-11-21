import requests
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates  # 추가됨
from pydantic import BaseModel

PROGRAM_ID = "CvqJNLw8FkMwni8GcK9r6L5MThpFMDAWhpiH21aPTuPH"  
SOLANA_RPC_URL = "https://api.devnet.solana.com"

templates = Jinja2Templates(directory="templates")

def get_candle_data(minute=1, coin="KRW-BTC", count=200):
    url = f"https://api.bithumb.com/v1/candles/minutes/{minute}?market={coin}&count={count}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['trade_price'] = pd.to_numeric(df['trade_price'])
        df = df.iloc[::-1].reset_index(drop=True) 
        final_df = df['trade_price'].tolist()
        return final_df
    else:
        print("Candle Chart API fail")
        return None

def get_trade_price(coin="KRW-BTC"):
    url = f"https://api.bithumb.com/v1/ticker?markets={coin}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 400:
        print("ERROR: get trade balance \n")
        return None

    data = response.json()[0]
    return float(data["trade_price"])

class GameResult(BaseModel):
    direction: str
    entry_price: float
    exit_price: float
    is_win: bool
    player_pubkey: str
    transaction_signature: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/current-price")
async def get_current_price():
    price = get_trade_price("KRW-SOL")
    return {"price": price}

@app.post("/api/verify-game")
async def verify_game(game_result: GameResult):
    """
    사용자가 전송한 트랜잭션을 검증
    """
    try:
        return {
            "success": True,
            "message": "Game result verified",
            "transaction": game_result.transaction_signature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/program-info")
async def get_program_info():
    """
    프론트엔드에서 트랜잭션을 구성하는데 필요한 정보 제공
    """
    return {
        "program_id": PROGRAM_ID,
        "rpc_url": SOLANA_RPC_URL
    }

@app.get("/", response_class=HTMLResponse)
async def get_chart_page(request: Request):
    trade_prices = get_candle_data(1, "KRW-SOL")

    if trade_prices is None:
        return HTMLResponse(content="<h3>데이터를 가져오는 데 실패했습니다. (API 오류)</h3>")

    labels = list(range(len(trade_prices)))
    
    # 템플릿에서 포맷팅하기 위해 현재가를 미리 계산해서 전달
    current_price_fmt = f"{trade_prices[-1]:,.0f}"

    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "trade_prices": trade_prices,
            "labels": labels,
            "current_price_fmt": current_price_fmt
        }
    )