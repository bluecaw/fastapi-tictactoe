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

// TTT
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
    const b = document.getElementById('ttt-board'); b.innerHTML = '';
    data.board.forEach((val, idx) => {
        const c = document.createElement('div'); c.className = 'ttt-cell'; c.innerText = val;
        c.onclick = () => moveTTT(idx); b.appendChild(c);
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

// DnB
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
    let html = '';
    html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[0] ? 'active' : ''}" onclick="moveDnB('h',0)"></div><div class="dot"></div><div class="h-line ${data.h_lines[1] ? 'active' : ''}" onclick="moveDnB('h',1)"></div><div class="dot"></div></div>`;
    html += `<div class="dnb-row"><div class="v-line ${data.v_lines[0] ? 'active' : ''}" onclick="moveDnB('v',0)"></div><div class="box">${data.boxes[0]}</div><div class="v-line ${data.v_lines[1] ? 'active' : ''}" onclick="moveDnB('v',1)"></div><div class="box">${data.boxes[1]}</div><div class="v-line ${data.v_lines[2] ? 'active' : ''}" onclick="moveDnB('v',2)"></div></div>`;
    html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[2] ? 'active' : ''}" onclick="moveDnB('h',2)"></div><div class="dot"></div><div class="h-line ${data.h_lines[3] ? 'active' : ''}" onclick="moveDnB('h',3)"></div><div class="dot"></div></div>`;
    html += `<div class="dnb-row"><div class="v-line ${data.v_lines[3] ? 'active' : ''}" onclick="moveDnB('v',3)"></div><div class="box">${data.boxes[2]}</div><div class="v-line ${data.v_lines[4] ? 'active' : ''}" onclick="moveDnB('v',4)"></div><div class="box">${data.boxes[3]}</div><div class="v-line ${data.v_lines[5] ? 'active' : ''}" onclick="moveDnB('v',5)"></div></div>`;
    html += `<div class="dnb-row"><div class="dot"></div><div class="h-line ${data.h_lines[4] ? 'active' : ''}" onclick="moveDnB('h',4)"></div><div class="dot"></div><div class="h-line ${data.h_lines[5] ? 'active' : ''}" onclick="moveDnB('h',5)"></div><div class="dot"></div></div>`;
    document.getElementById('dnb-board').innerHTML = html;
    document.getElementById('dnb-status').innerText = data.winner ? (data.winner === 'Draw' ? '引き分け！' : `勝者: ${data.winner} 🎉`) : `手番: ${data.turn} | P1: ${data.scores.P1}点 / P2: ${data.scores.P2}点`;
}
async function fetchDnBHistory() {
    const res = await fetch('/api/dnb/history');
    const history = await res.json();
    const listEl = document.getElementById('dnb-history-list');
    if (history.length === 0) { listEl.innerHTML = '<li>対戦履歴がありません</li>'; return; }
    listEl.innerHTML = history.map(h => `<li>P1(${h.p1_score}) - P2(${h.p2_score}) | 勝者: <strong>${h.winner}</strong> (${h.created_at})</li>`).join('');
}

// RPS
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

// Guess
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