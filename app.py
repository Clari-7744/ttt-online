"""
Main app file
"""
# pylint: disable=invalid-name
import json
import re
import uuid
import bs4
import flask
from checks_gets import end_check

app = flask.Flask(__name__)

games = {}
x = "XO"


@app.route("/")
def home():
    """index"""
    soup = bs4.BeautifulSoup(
        "<!DOCTYPE html><html><head><title>Tic-Tac-Toe Home</title></head></html>",
        "html.parser",
    )
    body = soup.new_tag("body")
    start_new = soup.new_tag(
        "input",
        id="start_new",
        type="button",
        value="Start New",
        onclick="location.href='/game';",
    )
    body.append(start_new)
    for gid, game in games.items():
        if len(game["players"]) != 1 or game["ended"][0] or not any(game["players"]):
            continue
        join_game_div = soup.new_tag("div", id="join_game_div")
        join_game_div.append(f"Player: {game['players'][0]}")
        join_game_div.append(
            soup.new_tag(
                "input",
                id="join_game",
                type="button",
                value="Join Game",
                onclick=f"location.href='/game?game={gid}';",
            )
        )
        body.append(join_game_div)
    soup.find("html").append(body)
    return soup.prettify()


@app.route("/game")
def active_game():
    """Active game"""
    soup = bs4.BeautifulSoup(
        open("game.html", "r", encoding="utf-8").read(), "html.parser"
    )
    body = soup.new_tag("body")
    name_div = soup.new_tag("div", id="div_name")
    name_div.append("Enter name ")
    name_input = soup.new_tag("input", id="input_name", type="text")
    name_submit = soup.new_tag(
        "input",
        id="submit_name",
        type="submit",
        value="Enter",
        onclick="setPlayer(document.getElementById('input_name').value.trim());",
    )
    name_div.append(name_input)
    name_div.append(name_submit)
    body.append(name_div)
    body.append(soup.new_tag("div", id="board_div"))
    body.append(soup.new_tag("div", id="turn_number"))

    gameid = flask.request.args.get("game", None)
    if (
        not gameid
        or not games.get(gameid)
        or len(games.get(gameid).get("players", [])) >= 2
    ):
        gameid = uuid.uuid1().hex
        games[gameid] = {
            "board": {"a": ["", "", ""], "b": ["", "", ""], "c": ["", "", ""]},
            "turn": False,
            "players": [],
            "ended": (False, False),
        }
    games[gameid]["players"].append("")
    for i, v in dict(
        game_id=gameid,
        player_num=len(games[gameid]["players"]),
        player_name="",
        opponent_name="",
    ).items():
        soup.find("head").append(soup.new_tag("meta", id=i, content=v))
    body.append(
        soup.new_tag(
            "input",
            type="button",
            value="Share",
            id="share_button",
            onclick=f"share('{gameid}');",
        )
    )
    soup.find("html").append(body)
    return soup.prettify()


@app.route("/setSpace")
def set_space():
    """
    Set space
    """
    game, user, space = [
        flask.request.args.get(x, None) for x in ["game", "user", "space"]
    ]
    if not (res := check_game(game))[0]:
        return res[1]
    if not (res := check_user(user))[0]:
        return res[1]
    if not space:
        return flask.Response(
            json.dumps({"message": "Space ID is required"}),
            status=400,
            mimetype="application/json",
        )
    if not re.match("[abcABC][123]", space):
        return flask.Response(
            json.dumps({"message": "Invalid space ID - must be `a1` to `c3`"}),
            status=400,
            mimetype="application/json",
        )
    game = games.get(game)
    if game["ended"][0]:
        return flask.Response(
            json.dumps({"message": "Game ended"}),
            status=400,
            mimetype="application/json",
        )
    s = game["turn"]
    if s and len(game["players"]) < 2:
        return flask.Response(
            json.dumps({"message": "Waiting for player 2..."}),
            status=400,
            mimetype="application/json",
        )
    if int(s) != game["players"].index(user):
        return flask.Response(
            json.dumps({"message": "Not your turn"}),
            status=400,
            mimetype="application/json",
        )
    if game["board"][space[0]][int(space[1]) - 1]:
        return flask.Response(
            json.dumps({"message": "Space already taken"}),
            status=400,
            mimetype="application/json",
        )
    game["board"][space[0]][int(space[1]) - 1] = x[s]
    game["turn"] = not s
    game["ended"] = end_check(game["board"], x[game["turn"] - 1])
    return flask.Response(
        json.dumps(
            {
                "move": x[s],
                "ended": game["ended"][0],
                "tie": game["ended"][1],
                "player": game["players"][s],
            }
        ),
        status=200,
        mimetype="application/json",
    )


@app.route("/setPlayer")
def set_player():
    """
    Set player
    """
    game, user, player_num = [
        flask.request.args.get(x, None).strip() for x in ["game", "user", "playerNum"]
    ]
    if not (res := check_game(game))[0]:
        return res[1]
    if user in games[game]["players"]:
        return flask.Response(
            json.dumps({"message": "Player already exists"}),
            status=400,
            mimetype="application/json",
        )
    games[game]["players"][int(player_num) - 1] = user
    return flask.Response(
        json.dumps({"message": "Player set"}), status=200, mimetype="application/json"
    )


@app.route("/checkWin")
def check_win():
    """
    Check win
    """
    game, user = [flask.request.args.get(x, None) for x in ["game", "user"]]
    if not (res := check_game(game))[0]:
        return res[1]
    if not (res := check_user(user))[0]:
        return res[1]
    game = games[game]
    print(game["board"])
    return flask.Response(
        json.dumps(
            {
                "won": end_check(game["board"], x[game["turn"]])[0],
                "message": game["players"][game["turn"]],
            }
        ),
        status=200,
        mimetype="application/json",
    )


@app.route("/getBoard")
def get_board():
    """
    Get board
    """
    game = flask.request.args.get("game", None)
    if not (res := check_game(game))[0]:
        return res[1]
    game = games[game]
    return flask.Response(
        json.dumps(game["board"]), status=200, mimetype="application/json"
    )


@app.route("/getGame")
def get_game():
    """
    Get game
    """
    game = flask.request.args.get("game", None)
    if not (res := check_game(game))[0]:
        return res[1]
    game = games[game]
    return flask.Response(json.dumps(game), status=200, mimetype="application/json")


@app.route("/purgeGames")
def purge_games():
    """
    Purge games
    """
    games = {}


@app.errorhandler(404)
def not_found(details):  # pylint: disable=unused-argument
    """404 page"""
    return "<meta http-equiv='Refresh' content=\"0; url='/?err_code=404'\">"


@app.route("/<string:img>.png")
def png(img=""):
    return open(
        img + ".png", "rb"
    ).read()  # ask how to retrieve local resource without...this


def check_game(game):
    if not game:
        return False, flask.Response(
            json.dumps({"message": "No game specified"}),
            status=400,
            mimetype="application/json",
        )
    if not games.get(game):
        return False, flask.Response(
            json.dumps({"message": "Game does not exist"}),
            status=404,
            mimetype="application/json",
        )
    return True, None


def check_user(user):
    if not user:
        return False, flask.Response(
            json.dumps({"message": "Username is required"}),
            status=400,
            mimetype="application/json",
        )
    return True, None


app.run(port=7744, debug=True)
