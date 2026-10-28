function openNav() { document.getElementById("mySidebar").style.width = "250px"; }
function closeNav() { document.getElementById("mySidebar").style.width = "0"; }

function switchGame(key) {
    closeNav();
    document.querySelectorAll('.game-container').forEach(el => el.classList.remove('active'));
    if (key === 'ttt') {
        document.getElementById('game-ttt').classList.add('active');
        document.getElementById('title').innerText = 'まるばつゲーム';
        fetchTTT();
    } else if (key === 'dnb') {
        document.getElementById('game-dnb').classList.add('active');
        document.getElementById('title').innerText = '線引き陣取り';
        fetchDnB();
    } else if (key === 'rps') {
        document.getElementById('game-rps').classList.add('active');
        document.getElementById('title').innerText = 'じゃんけん連勝バトル';
        fetchRPS();
    } else if (key === 'guess') {
        document.getElementById('game-guess').classList.add('active');
        document.getElementById('title').innerText = '数字当てゲーム';
        fetchGuess();
    }
}

// TTT (まるばつゲーム)
async function fetchTTT() {
    renderTTT(await (await fetch('/api/ttt')).json());
    fetchTTTHistory();
}
async function moveTTT(idx) {
    const res = await (await fetch('/api/ttt/move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx }) })).json();
    renderTTT(res);
    if (res.winner) { fetchTTTHistory(); }
}
async function resetTTT() { renderTTT(await (await fetch('/api/ttt/reset', { method: 'POST' })).json()); }

function renderTTT(data) {
    const b = document.getElementById('ttt-board'); 
    b.innerHTML = '';
    data.board.forEach((val, idx) => {
        const c = document.createElement('div'); 
        c.className = 'ttt-cell'; 
        c.innerText = val;
        // 🔒 CSP対応: onclick属性ではなく addEventListener を使用
        c.addEventListener('click', () => moveTTT(idx));
        b.appendChild(c);
    });
    document.getElementById('ttt-status').innerText = data.winner ? (data.winner === 'Draw' ? '引き分け！' : `勝者: ${data.winner} 🎉`) : `現在の手番: ${data.turn}`;
}

async function fetchTTTHistory() {
    const res = await fetch('/api/ttt/history');
    const history = await res.json();
    const listEl = document.getElementById('ttt-history-list');
    if (history.length === 0) { listEl.innerHTML = '<li>対戦履歴がありません</li>'; return; }
    listEl.innerHTML = history.map(h => `<li>勝者: <strong>${h.winner === 'Draw' ? '引き分け' : h.winner + 'の勝ち'}</strong> (${h.created_at})</li>`).join('');
}

// DnB (線引き陣取り) - 完全DOM生成によるCSP対応
async function fetchDnB() {
    renderDnB(await (await fetch('/api/dnb')).json());
    fetchDnBHistory();
}
async function moveDnB(type, idx) {
    const res = await (await fetch('/api/dnb/move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: type, index: idx }) })).json();
    renderDnB(res);
    if (res.winner) { fetchDnBHistory(); }
}
async function resetDnB() { renderDnB(await (await fetch('/api/dnb/reset', { method: 'POST' })).json()); }

function renderDnB(data) {
    const boardEl = document.getElementById('dnb-board');
    boardEl.innerHTML = '';

    // 補助関数: 横線要素の作成
    function createHLine(idx) {
        const line = document.createElement('div');
        line.className = 'h-line';
        
        // データの値（例: null, 'P1', 'P2', または true/false など）に応じた処理
        const owner = data.h_lines[idx]; 
        if (owner) {
            line.classList.add('active');
            // 'P1' なら p1クラス、'P2' なら p2クラスを付与
            if (owner === 'P1' || owner === 1) line.classList.add('p1');
            else if (owner === 'P2' || owner === 2) line.classList.add('p2');
            else line.classList.add('p1'); // 単なる真偽値の場合はデフォルトでp1扱い
        }

        line.addEventListener('click', () => moveDnB('h', idx));
        return line;
    }

    // 補助関数: 縦線要素の作成
    function createVLine(idx) {
        const line = document.createElement('div');
        line.className = 'v-line';
        
        const owner = data.v_lines[idx];
        if (owner) {
            line.classList.add('active');
            if (owner === 'P1' || owner === 1) line.classList.add('p1');
            else if (owner === 'P2' || owner === 2) line.classList.add('p2');
            else line.classList.add('p1');
        }

        line.addEventListener('click', () => moveDnB('v', idx));
        return line;
    }

    // 補助関数: ドット要素の作成
    function createDot() {
        const dot = document.createElement('div');
        dot.className = 'dot';
        return dot;
    }

    // 補助関数: ボックス要素の作成
    function createBox(idx) {
        const box = document.createElement('div');
        box.className = 'box';
        
        const boxOwner = data.boxes[idx]; // 例: 'P1', 'P2', または空文字
        if (boxOwner) {
            box.innerText = boxOwner;
            if (boxOwner === 'P1') box.classList.add('p1');
            else if (boxOwner === 'P2') box.classList.add('p2');
        } else {
            box.innerText = '';
        }

        return box;
    }

    // --- 以下、行の組み立て（変更なし） ---
    const row1 = document.createElement('div');
    row1.className = 'dnb-row';
    row1.appendChild(createDot());
    row1.appendChild(createHLine(0));
    row1.appendChild(createDot());
    row1.appendChild(createHLine(1));
    row1.appendChild(createDot());
    boardEl.appendChild(row1);

    const row2 = document.createElement('div');
    row2.className = 'dnb-row';
    row2.appendChild(createVLine(0));
    row2.appendChild(createBox(0));
    row2.appendChild(createVLine(1));
    row2.appendChild(createBox(1));
    row2.appendChild(createVLine(2));
    boardEl.appendChild(row2);

    const row3 = document.createElement('div');
    row3.className = 'dnb-row';
    row3.appendChild(createDot());
    row3.appendChild(createHLine(2));
    row3.appendChild(createDot());
    row3.appendChild(createHLine(3));
    row3.appendChild(createDot());
    boardEl.appendChild(row3);

    const row4 = document.createElement('div');
    row4.className = 'dnb-row';
    row4.appendChild(createVLine(3));
    row4.appendChild(createBox(2));
    row4.appendChild(createVLine(4));
    row4.appendChild(createBox(3));
    row4.appendChild(createVLine(5));
    boardEl.appendChild(row4);

    const row5 = document.createElement('div');
    row5.className = 'dnb-row';
    row5.appendChild(createDot());
    row5.appendChild(createHLine(4));
    row5.appendChild(createDot());
    row5.appendChild(createHLine(5));
    row5.appendChild(createDot());
    boardEl.appendChild(row5);

    document.getElementById('dnb-status').innerText = data.winner ? (data.winner === 'Draw' ? '引き分け！' : `勝者: ${data.winner} 🎉`) : `手番: ${data.turn} | P1: ${data.scores.P1}点 / P2: ${data.scores.P2}点`;
}

async function fetchDnBHistory() {
    const res = await fetch('/api/dnb/history');
    const history = await res.json();
    const listEl = document.getElementById('dnb-history-list');
    if (history.length === 0) { listEl.innerHTML = '<li>対戦履歴がありません</li>'; return; }
    listEl.innerHTML = history.map(h => `<li>P1(${h.p1_score}) - P2(${h.p2_score}) | 勝者: <strong>${h.winner}</strong> (${h.created_at})</li>`).join('');
}

// RPS (じゃんけん)
async function fetchRPS() {
    renderRPS(await (await fetch('/api/rps')).json());
    fetchRPSRanking();
}
async function playRPS(hand) {
    const res = await (await fetch('/api/rps/play', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hand: hand }) })).json();
    renderRPS(res);
    if (res.result === 'Lose') { fetchRPSRanking(); }
}
async function resetRPS() { renderRPS(await (await fetch('/api/rps/reset', { method: 'POST' })).json()); }

function renderRPS(data) {
    document.getElementById('rps-status').innerText = `現在の連勝数: ${data.streak} (最高: ${data.max_streak})`;
    let resText = '';
    if (data.result) {
        const symbols = { 'rock': '✊', 'paper': '✋', 'scissors': '✌️' };
        resText = `あなた: ${symbols[data.last_user]} vs 相手: ${symbols[data.last_cpu]} → `;
        if (data.result === 'Win') resText += 'あなたの勝ち！ 🎉';
        else if (data.result === 'Lose') resText += 'あなたの負け... 😢';
        else resText += 'あいこ！';
    }
    document.getElementById('rps-result').innerHTML = resText;
}

async function fetchRPSRanking() {
    const res = await fetch('/api/rps/ranking');
    const ranking = await res.json();
    const listEl = document.getElementById('rps-ranking-list');
    if (ranking.length === 0) { listEl.innerHTML = '<li>ランキング記録がありません</li>'; return; }
    listEl.innerHTML = ranking.map((r, i) => `<li>第${i + 1}位: <strong>${r.streak}連勝</strong> (${r.created_at})</li>`).join('');
}

// Guess (数字当て)
async function fetchGuess() {
    const res = await (await fetch('/api/guess')).json();
    renderGuess(res);
    fetchRanking();
}
async function playGuess() {
    const val = parseInt(document.getElementById('guess-input').value);
    if (isNaN(val)) return;
    const res = await (await fetch('/api/guess/play', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ number: val }) })).json();
    renderGuess(res);
    document.getElementById('guess-input').value = '';
    if (res.clear) { fetchRanking(); }
}
async function resetGuess() {
    const res = await (await fetch('/api/guess/reset', { method: 'POST' })).json();
    renderGuess(res);
}
function renderGuess(data) {
    document.getElementById('guess-status').innerHTML = `${data.message}<br><small>試行回数: ${data.attempts}回</small>`;
}
async function fetchRanking() {
    const res = await fetch('/api/guess/ranking');
    const ranking = await res.json();
    const listEl = document.getElementById('ranking-list');
    if (ranking.length === 0) {
        listEl.innerHTML = '<li>まだクリア記録がありません</li>';
        return;
    }
    let html = '';
    ranking.forEach((r, i) => {
        html += `<li>第${i + 1}位: <strong>${r.attempts}回</strong> (${r.created_at})</li>`;
    });
    listEl.innerHTML = html;
}

// --- イベントリスナーの登録（CSP対応） ---

// ハンバーガーメニューの開閉
document.getElementById('open-sidebar').addEventListener('click', openNav);
document.getElementById('close-sidebar').addEventListener('click', closeNav);

// サイドバーのゲーム切り替えリンク
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        const gameKey = e.target.getAttribute('data-game');
        switchGame(gameKey);
    });
});

// 各種リセットボタン
document.getElementById('reset-ttt').addEventListener('click', resetTTT);
document.getElementById('reset-dnb').addEventListener('click', resetDnB);
document.getElementById('reset-rps').addEventListener('click', resetRPS);
document.getElementById('reset-guess').addEventListener('click', resetGuess);

// じゃんけんボタン
document.querySelectorAll('.rps-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const hand = e.target.getAttribute('data-hand');
        playRPS(hand);
    });
});

// 数字当て送信ボタン
document.getElementById('guess-submit').addEventListener('click', playGuess);

// 初期ロード時に最初のゲーム（まるばつ）の履歴を取得
fetchTTT();