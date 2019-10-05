import requests
import redis
import pickle
import os
from config import Config

from flask import Flask
from flask_discord import DiscordOAuth2Session

app_config = Config()
app = Flask(__name__)
app.secret_key = os.urandom(24)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
app.config["DISCORD_CLIENT_ID"] = app_config.client_id
app.config["DISCORD_CLIENT_SECRET"] = app_config.client_secret
app.config["DISCORD_REDIRECT_URI"] = app_config.redirect_uri


db = redis.Redis(host=app_config.redis_host, port=6379, db=0)


discord = DiscordOAuth2Session(app)


def get_account_sr(accounts):
    s = requests.Session()
    for account in accounts:
        account_info = s.get(f"https://ow-api.com/v1/stats/pc/eu/{account['bnet'].replace('#', '-')}/profile").json()
        account["private"] = account_info["private"]
        if not account_info["private"]:
            account["tank"] = False
            account["damage"] = False
            account["support"] = False
            if account_info["ratings"]:
                for rating in account_info["ratings"]:
                    account[rating["role"]] = rating["level"]
    return accounts


def set_eligible(accounts):
    for account in accounts:
        if account["tank"] >= 2500 or account["damage"] >= 2500 or account["support"] >= 2500:
            account["eligible"] = False
        elif not account["tank"] and not account["damage"] and not account["support"]:
            account["eligible"] = False
        else:
            account["eligible"] = True
    return accounts


def get_battlenet_accounts(discord_accounts):
    battlenet_accounts = [account for account in discord_accounts if account["type"] == "battlenet"]
    battlenet_accounts = [{"bnet": account["id"]} for account in battlenet_accounts]
    battlenet_accounts = get_account_sr(battlenet_accounts)
    battlenet_accounts = set_eligible(battlenet_accounts)
    return battlenet_accounts


@app.route("/")
def authorize():
    return discord.create_session(["identify", "connections"])


@app.route("/callback/")
def callback():
    discord.callback()
    user = discord.fetch_user()
    user_battlenet_accounts = get_battlenet_accounts(discord.get("/users/@me/connections"))
    if user_battlenet_accounts:
        db.set(str(user.id), pickle.dumps(user_battlenet_accounts))
        discord.revoke()
        return "Done! You can now close this window!"
    else:
        return "You don't have a battle.net account linked! Please link your battle.net account to your discord to continue."


if __name__ == "__main__":
    app.run()
