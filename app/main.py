from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.database import init_db
from app.routers import dnb, guess, rps, ttt
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
  # サーバー起動時にデータベースとテーブルを初期化
  init_db()
  yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 🆕 セキュリティヘッダーを追加するミドルウェア（ここに追加）
@app.middleware("http")
async def add_security_headers(request, call_next):
  response = await call_next(request)
  response.headers["Strict-Transport-Security"] = (
      "max-age=63072000; includeSubDomains; preload"
  )
  response.headers["X-Content-Type-Options"] = "nosniff"
  response.headers["X-Frame-Options"] = "SAMEORIGIN"
  response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
  response.headers["Content-Security-Policy"] = (
      "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src"
      " 'self';"
  )
  return response

# 各ゲームのルーター登録
app.include_router(ttt.router)
app.include_router(dnb.router)
app.include_router(rps.router)
app.include_router(guess.router)


@app.get("/", response_class=HTMLResponse)
def index():
  return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FastAPI ミニゲームポータル</title>
        <style>
            body { font-family: sans-serif; text-align: center; margin: 0; padding: 0; background: #f4f4f9; }
            header { background: #333; color: white; padding: 15px; display: flex; align-items: center; }
            .menu-btn { font-size: 24px; cursor: pointer; background: none; border: none; color: white; margin-right: 15px; }
            .sidebar { height: 100%; width: 0; position: fixed; z-index: 10; top: 0; left: 0; background-color: #111; overflow-x: hidden; transition: 0.3s; padding-top: 60px; text-align: left; }
            .sidebar a { padding: 15px 25px; text-decoration: none; font-size: 18px; color: #818181; display: block; transition: 0.2s; }
            .sidebar a:hover { color: #f1f1f1; background: #222; }
            .sidebar .close-btn { position: absolute; top: 10px; right: 20px; font-size: 30px; }

            .content { padding: 20px; }
            .game-container { display: none; }
            .game-container.active { display: block; }

            .status { font-size: 18px; margin: 15px; font-weight: bold; color: #444; }
            button.reset-btn { padding: 8px 16px; font-size: 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 15px; }

            /* まるばつ */
            .ttt-board { display: grid; grid-template-columns: repeat(3, 90px); gap: 5px; justify-content: center; margin: 20px auto; }
            .ttt-cell { width: 90px; height: 90px; background: white; font-size: 36px; font-weight: bold; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 2px solid #ccc; border-radius: 8px; }

            /* ドット＆ボックス */
            .dnb-board { display: inline-block; margin: 20px auto; }
            .dnb-row { display: flex; align-items: center; justify-content: center; }
            .dot { width: 12px; height: 12px; background: #333; border-radius: 50%; }
            .h-line { width: 60px; height: 8px; background: #ddd; cursor: pointer; margin: 0 2px; border-radius: 4px; }
            .h-line.active { background: #007bff; }
            .v-line { width: 8px; height: 60px; background: #ddd; cursor: pointer; margin: 2px 0; border-radius: 4px; }
            .v-line.active { background: #007bff; }
            .box { width: 60px; height: 60px; background: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }

            /* じゃんけん */
            .rps-btns button { font-size: 24px; padding: 15px 25px; margin: 10px; cursor: pointer; border-radius: 10px; border: 2px solid #ccc; background: white; }
            .rps-btns button:hover { background: #e2e2e2; }

            /* 数字当て */
            .guess-box input { padding: 10px; font-size: 18px; width: 120px; text-align: center; }
            .guess-box button { padding: 10px 20px; font-size: 18px; background: #007bff; color: white; border: none; cursor: pointer; }
            .ranking-box { margin-top: 20px; background: white; padding: 10px; display: inline-block; border-radius: 8px; border: 1px solid #ddd; text-align: left; }
        </style>
    </head>
    <body>
        <div id="mySidebar" class="sidebar">
            <a href="javascript:void(0)" class="close-btn" onclick="closeNav()">&times;</a>
            <a href="javascript:void(0)" onclick="switchGame('ttt')">⭕❌ まるばつゲーム</a>
            <a href="javascript:void(0)" onclick="switchGame('dnb')">🔳 線引き陣取り</a>
            <a href="javascript:void(0)" onclick="switchGame('rps')">✌️ じゃんけん連勝バトル</a>
            <a href="javascript:void(0)" onclick="switchGame('guess')">🔢 数字当てゲーム</a>
        </div>

        <header>
            <button class="menu-btn" onclick="openNav()">&#9776;</button>
            <h2 id="title" style="margin:0;">まるばつゲーム</h2>
        </header>

        <div class="content">
            <!-- 1. まるばつゲーム -->
            <div id="game-ttt" class="game-container active">
                <div id="ttt-status" class="status">読み込み中...</div>
                <div class="ttt-board" id="ttt-board"></div>
                <button class="reset-btn" onclick="resetTTT()">リセット</button>
                <div style="margin-top:20px;">
                    <div class="ranking-box">
                        <strong>📋 直近の対戦履歴 (5件)</strong>
                        <ul id="ttt-history-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>

            <!-- 2. ドット＆ボックス -->
            <div id="game-dnb" class="game-container">
                <div id="dnb-status" class="status">読み込み中...</div>
                <div id="dnb-board" class="dnb-board"></div>
                <button class="reset-btn" onclick="resetDnB()">リセット</button>
                <div style="margin-top:20px;">
                    <div class="ranking-box">
                        <strong>📋 直近の対戦履歴 (5件)</strong>
                        <ul id="dnb-history-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>

            <!-- 3. じゃんけん連勝バトル -->
            <div id="game-rps" class="game-container">
                <div id="rps-status" class="status">読み込み中...</div>
                <div class="rps-btns">
                    <button onclick="playRPS('rock')">✊ グー</button>
                    <button onclick="playRPS('paper')">✋ パー</button>
                    <button onclick="playRPS('scissors')">✌️ チョキ</button>
                </div>
                <div id="rps-result" style="font-size: 20px; margin-top: 15px;"></div>
                <button class="reset-btn" onclick="resetRPS()">リセット</button>
                <div style="margin-top:20px;">
                    <div class="ranking-box">
                        <strong>🏆 連勝ランキング (上位5件)</strong>
                        <ul id="rps-ranking-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>

            <!-- 4. 数字当てゲーム -->
            <div id="game-guess" class="game-container">
                <div id="guess-status" class="status">読み込み中...</div>
                <div class="guess-box">
                    <input type="number" id="guess-input" min="1" max="100" placeholder="1〜100">
                    <button onclick="playGuess()">送信</button>
                </div>
                <br>
                <button class="reset-btn" onclick="resetGuess()">リセット</button>
                <div>
                    <div class="ranking-box">
                        <strong>🏆 クリアランキング (上位5件)</strong>
                        <ul id="ranking-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>
        </div>

        <script src="/static/main.js"></script>
    </body>
    </html>
    """