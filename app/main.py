from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from app.database import init_db
from app.routers import dnb, guess, rps, ttt
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
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
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self';"
    )
    return response

# 各ゲームのルーター登録
app.include_router(ttt.router)
app.include_router(dnb.router)
app.include_router(rps.router)
app.include_router(guess.router)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
        <rect width="64" height="64" rx="14" fill="#333333"/>
        <path d="M16 22 H48 C53 22 56 26 55 31 L52 46 C51 49 47 51 44 49 L37 44 H27 L20 49 C17 51 13 49 12 46 L9 31 C8 26 11 22 16 22 Z" fill="#007bff"/>
        <rect x="18" y="32" width="10" height="3" fill="#ffffff" rx="1"/>
        <rect x="21.5" y="28.5" width="3" height="10" fill="#ffffff" rx="1"/>
        <circle cx="41" cy="35" r="2.5" fill="#ff4757"/>
        <circle cx="46" cy="31" r="2.5" fill="#ffa502"/>
    </svg>"""
    return Response(content=svg_code, media_type="image/svg+xml")

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FastAPI ミニゲームポータル</title>
        <link rel="icon" type="image/svg+xml" href="/favicon.ico">
<style>
            body { font-family: sans-serif; text-align: center; margin: 0; padding: 0; background: #f0f9ff; color: #0f172a; min-height: 100vh; position: relative; overflow-x: hidden; }
            header { background: linear-gradient(135deg, #0284c7, #0369a1); color: white; padding: 15px; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); position: relative; z-index: 2; }
            .menu-btn { font-size: 24px; cursor: pointer; background: none; border: none; color: white; margin-right: 15px; }
            
            .sidebar { height: 100%; width: 0; position: fixed; z-index: 10; top: 0; left: 0; background-color: #0f172a; overflow-x: hidden; transition: 0.3s; padding-top: 60px; text-align: left; }
            .sidebar a { padding: 15px 25px; text-decoration: none; font-size: 18px; color: #94a3b8; display: block; transition: 0.2s; }
            .sidebar a:hover { color: #f8fafc; background: #1e293b; }
            .sidebar .close-btn { position: absolute; top: 10px; right: 20px; font-size: 30px; }

            .content { padding: 20px; position: relative; z-index: 2; }
            .game-container { display: none; }
            .game-container.active { display: block; }

            .status { font-size: 18px; margin: 15px; font-weight: bold; color: #0369a1; }
            button.reset-btn { padding: 8px 16px; font-size: 15px; background: #0ea5e9; color: white; border: none; border-radius: 6px; cursor: pointer; margin-top: 15px; transition: background 0.2s; }
            button.reset-btn:hover { background: #0284c7; }

            /* まるばつ */
            .ttt-board { display: grid; grid-template-columns: repeat(3, 90px); gap: 6px; justify-content: center; margin: 20px auto; }
            .ttt-cell { width: 90px; height: 90px; background: white; font-size: 36px; font-weight: bold; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 2px solid #bae6fd; border-radius: 10px; box-shadow: 0 2px 4px rgba(2,132,199,0.05); }
            .ttt-cell:hover { background: #f8fafc; border-color: #0ea5e9; }

            /* ドット＆ボックス */
            .dnb-board { display: inline-block; margin: 20px auto; }
            .dnb-row { display: flex; align-items: center; justify-content: center; }
            .dot { width: 12px; height: 12px; background: #0369a1; border-radius: 50%; }
            .h-line { width: 60px; height: 8px; background: #e0f2fe; cursor: pointer; margin: 0 2px; border-radius: 4px; }
            .h-line.active { background: #0284c7; }
            .v-line { width: 8px; height: 60px; background: #e0f2fe; cursor: pointer; margin: 2px 0; border-radius: 4px; }
            .v-line.active { background: #0284c7; }
            .box { width: 60px; height: 60px; background: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; border-radius: 4px; border: 1px solid #bae6fd; }

            /* じゃんけん */
            .rps-btns button { font-size: 24px; padding: 15px 25px; margin: 10px; cursor: pointer; border-radius: 12px; border: 2px solid #bae6fd; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .rps-btns button:hover { background: #e0f2fe; border-color: #0ea5e9; }

            /* 数字当て */
            .guess-box input { padding: 10px; font-size: 18px; width: 120px; text-align: center; border: 2px solid #bae6fd; border-radius: 6px; outline: none; }
            .guess-box input:focus { border-color: #0284c7; }
            .guess-box button { padding: 10px 20px; font-size: 18px; background: #0284c7; color: white; border: none; border-radius: 6px; cursor: pointer; }
            .guess-box button:hover { background: #0369a1; }
            
            .ranking-box { margin-top: 20px; background: white; padding: 15px; display: inline-block; border-radius: 12px; border: 1px solid #bae6fd; text-align: left; box-shadow: 0 4px 6px rgba(2,132,199,0.05); }

            /* --- 🌊 背景SVG用アニメーションとレイアウト --- */
            .bg-svg-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; pointer-events: none; overflow: hidden; }
            .bg-svg { width: 100%; height: 100%; }

            @keyframes wave-move {
                0% { transform: translateX(0); }
                50% { transform: translateX(-2%); }
                100% { transform: translateX(0); }
            }
            .bg-waves {
                animation: wave-move 6s ease-in-out infinite;
            }
        </style>
    </head>
    <body>
        <div class="bg-svg-container">
            <svg class="bg-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMax slice">
                <!-- ゆるやかに動く水面 -->
                <g class="bg-waves" opacity="0.7">
                    <path d="M-100,400 C100,350 300,450 500,400 C700,350 900,450 1100,400 L1100,1000 L-100,1000 Z" fill="#bae6fd"/>
                    <path d="M-100,450 C150,390 350,510 550,450 C750,390 950,510 1100,450 L1100,1000 L-100,1000 Z" fill="#7dd3fc"/>
                    <path d="M-100,500 C80,470 280,530 480,500 C680,470 880,530 1100,500 L1100,1000 L-100,1000 Z" fill="#38bdf8"/>
                </g>

                <!-- もっと細かくごつごつした岩場（多層構造） -->
                <g>
                    <!-- 奥の暗い岩層 -->
                    <path d="M0,820 L30,790 L70,830 L110,780 L160,840 L210,800 L270,850 L320,810 L380,860 L430,820 L490,870 L540,830 L600,880 L660,840 L710,890 L770,840 L830,900 L880,850 L940,910 L1000,860 L1000,1000 L0,1000 Z" fill="#334155"/>
                    <!-- 手前の細かいごつごつした岩層 -->
                    <path d="M0,880 L40,850 L80,910 L130,860 L180,920 L240,870 L290,930 L350,880 L410,940 L460,890 L520,950 L580,900 L630,960 L690,910 L750,970 L800,920 L860,980 L920,930 L970,990 L1000,950 L1000,1000 L0,1000 Z" fill="#475569"/>
                    <!-- 最手前のエッジの効いた岩のハイライト層 -->
                    <path d="M0,930 L50,910 L90,960 L150,920 L200,970 L260,930 L320,980 L380,940 L440,990 L500,950 L560,1000 L620,950 L680,990 L740,940 L810,990 L870,950 L930,1000 L1000,970 L1000,1000 L0,1000 Z" fill="#64748b" opacity="0.8"/>
                </g>
            </svg>
        </div>

        <div id="mySidebar" class="sidebar">
            <a href="#" class="close-btn" id="close-sidebar">&times;</a>
            <a href="#" class="nav-link" data-game="ttt">⭕❌ まるばつゲーム</a>
            <a href="#" class="nav-link" data-game="dnb">🔳 線引き陣取り</a>
            <a href="#" class="nav-link" data-game="rps">✌️ じゃんけん連勝バトル</a>
            <a href="#" class="nav-link" data-game="guess">🔢 数字当てゲーム</a>
        </div>

        <header>
            <button class="menu-btn" id="open-sidebar">&#9776;</button>
            <h2 id="title" style="margin:0;">まるばつゲーム</h2>
        </header>

        <div class="content">
            <div id="game-ttt" class="game-container active">
                <div id="ttt-status" class="status">読み込み中...</div>
                <div class="ttt-board" id="ttt-board"></div>
                <button class="reset-btn" id="reset-ttt">リセット</button>
                <div style="margin-top:20px;">
                    <div class="ranking-box">
                        <strong>📋 直近の対戦履歴 (5件)</strong>
                        <ul id="ttt-history-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>

            <div id="game-dnb" class="game-container">
                <div id="dnb-status" class="status">読み込み中...</div>
                <div id="dnb-board" class="dnb-board"></div>
                <button class="reset-btn" id="reset-dnb">リセット</button>
                <div style="margin-top:20px;">
                    <div class="ranking-box">
                        <strong>📋 直近の対戦履歴 (5件)</strong>
                        <ul id="dnb-history-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>

            <div id="game-rps" class="game-container">
                <div id="rps-status" class="status">読み込み中...</div>
                <div class="rps-btns">
                    <button class="rps-btn" data-hand="rock">✊ グー</button>
                    <button class="rps-btn" data-hand="paper">✋ パー</button>
                    <button class="rps-btn" data-hand="scissors">✌️ チョキ</button>
                </div>
                <div id="rps-result" style="font-size: 20px; margin-top: 15px;"></div>
                <button class="reset-btn" id="reset-rps">リセット</button>
                <div style="margin-top:20px;">
                    <div class="ranking-box">
                        <strong>🏆 連勝ランキング (上位5件)</strong>
                        <ul id="rps-ranking-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>

            <div id="game-guess" class="game-container">
                <div id="guess-status" class="status">読み込み中...</div>
                <div class="guess-box">
                    <input type="number" id="guess-input" min="1" max="100" placeholder="1〜100">
                    <button id="guess-submit">送信</button>
                </div>
                <br>
                <button class="reset-btn" id="reset-guess">リセット</button>
                <div>
                    <div class="ranking-box">
                        <strong>🏆 クリアランキング (上位5件)</strong>
                        <ul id="ranking-list" style="margin: 5px 0 0 20px; padding:0;">読み込み中...</ul>
                    </div>
                </div>
            </div>
        </div>

        <script src="/static/script.js"></script>
    </body>
    </html>
    """