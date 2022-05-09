function createElement(name, options) {
    let element = document.createElement(name);
    for (let [k, v] of Object.entries(options))
        element.setAttribute(k, v);
    return element
}
async function setSpace(elem) {
    let args = `game=${document.getElementById('game_id').content}&space=${elem}`;
    let n = document.getElementById('player_name').content
    if (n) args += `&user=${n}`;
    let resp = await fetch(`${document.location.origin}/setSpace?${args}`)
    let s = resp.status;
    resp = await resp.json();
    if (s != 200) {
        return alert(resp.message);
    }
    document.getElementById(elem).innerHTML = resp.move;
}
async function setPlayer(name) {
    let gid = document.getElementById('game_id').content;
    resp = await fetch(`${document.location.origin}/setPlayer?game=${gid}&user=${name}&playerNum=${document.getElementById('player_num').content}`);
    s = resp.status;
    resp = await resp.json();
    if (s != 200) {
        return alert(resp.message);
    }
    document.getElementById('share_button').removeAttribute('disabled');
    document.getElementById('div_name').innerHTML = `Username: ${name}`
    document.getElementById('div_opponent').innerHTML = `Opponent: Waiting for opponent...`
    document.getElementById('player_name').content = name;
    let on = document.getElementById('opponent_name');
    let ended = [false, false];
    while (!ended[0]) {
        await buildBoard(gid);
        document.getElementById('turn_number').innerHTML = `Turn: Player ${resp.turn + 1 || 1}`;
        await new Promise(r => setTimeout(r, 1000));
        resp = await fetch(`${document.location.origin}/getGame?game=${gid}`).then(r => r.json());
        if (resp.players.every(e => e) && !on.content && resp.players.length > 1) {
            on.content = resp.players.filter(p => p != name)[0];
            let pl = (n) => `${n} (Player ${resp.players.indexOf(n) + 1})`;
    document.getElementById('div_name').innerHTML = `Username: ${pl(name)}`
            document.getElementById('div_opponent').innerHTML = `Opponent: ${pl(on.content)}`;
            document.getElementById('share_button').remove();
        }
        ended = resp.ended;
    }
    alert("Game ended!\n" + (resp.ended[1] ? "Tie game!" : resp.players[resp.turn] + " wins!"));
}
async function buildBoard(game) {
    let resp = await fetch(`${document.location.origin}/getBoard?game=${game}`);
    s = resp.status;
    resp = await resp.json();
    if (s != 200) {
        return alert(resp.message);
    }
    let board = document.getElementById('board_div');
    board.innerHTML = "";
    let table = createElement('table', { id: 'board_table' });
    for (let r of "abc") {
        let row = createElement('tr', { id: `row_${r}` });
        for (let [i, c] of Object.entries("123")) {
            let col = createElement('td', { id: `${r}${c}` });
            if (!resp[r][i])
                col.appendChild(createElement("input", { type: 'button', id: `${r}${c}b`, value: " ", onclick: `setSpace("${r}${c}")`, class: "ttt_space" }));
            else {
                col.innerHTML = resp[r][i];
            }
            row.appendChild(col);
            table.appendChild(row);
        }
    }
    board.appendChild(table);

}
function share(game) {
    let url = `${document.location.origin}/game?game=${game}`;
    const elem = document.createElement('textarea');
    elem.value = `Play TicTacToe with ${document.getElementById('player_name').content}! Join at ${url}`;
    document.body.appendChild(elem);
    elem.select();
    elem.setSelectionRange(0, 99999);
    document.execCommand('copy');
    document.body.removeChild(elem);
    alert('Copied link to clipboard');
}