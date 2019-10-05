import redis
import pickle
from config import Config

import discord
from discord.ext import commands, tasks

bot_config = Config()
bot = commands.Bot(command_prefix="%!")
db = redis.Redis(host=bot_config.redis_host, port=6379, db=0)

sorry_message = """
Sorry, you're not eligible to receive the Beginner role automatically. This is because you're either too high or are not placed this season.
If you are placed and at least one role is below 2550 and all roles are below 2750 contact a staff member to get the role manually.
"""

rule_message = """
You have been given the Beginner role.
Remember, you're only allowed to play in Beginner PUGs if all your roles are below 2750 and at least one role is below 2550!
Smurfing will result in a permanent ban from this Discord.
"""


@tasks.loop(seconds=5.0)
async def update_user_status():
    await bot.wait_until_ready()
    for key in db.keys():
        if key.isdigit():
            accounts = pickle.loads(db.get(key))
            eligible = True in [account["eligible"] for account in accounts]
            eligible_string = "Yes" if eligible else "No"
            color = 0x2dbd5b if eligible else 0xe80c22
            embed = discord.Embed(title="Eligible", description=eligible_string, color=color)
            if eligible:
                for account in accounts:
                    if account["eligible"]:
                        embed.add_field(name=account["bnet"], value="👍")
                    elif account["private"]:
                        embed.add_field(name=account["bnet"], value="Private")
                    else:
                        embed.add_field(name=account["bnet"], value="Not placed")
                embed.add_field(name="Remember the rules", value=rule_message)
                await bot.get_user(int(key)).send(embed=embed)

                user_guild = bot.get_guild(bot_config.guild_id)
                target_role = user_guild.get_role(bot_config.role_id)
                member = await user_guild.fetch_member(int(key))
                await member.add_roles(target_role)
                print("done")

            else:
                embed.add_field(name="Not eligible", value=sorry_message)
                await bot.get_user(int(key)).send(embed=embed)
            db.delete(key)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id != bot.user.id:
        user = bot.get_guild(bot_config.guild_id).get_member(payload.user_id)
        if payload.message_id == bot_config.reaction_message_id:
            if payload.emoji.name == bot_config.target_emoji:
                embed = discord.Embed(title="Verify your beginner status",
                                      description="[Click here](http://127.0.0.1:5000/) to verify that you're a beginner",
                                      color=0x4284f5)
                embed.set_footer(text="After verifying your rank, all data and authorizations are automatically removed")
                await user.send(embed=embed)
            reacted_message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            await reacted_message.remove_reaction(payload.emoji, user)


@bot.event
async def on_ready():
    print("ready")
    target_message = await bot.get_channel(bot_config.reaction_message_channel_id).fetch_message(bot_config.reaction_message_id)
    await target_message.add_reaction(bot_config.target_emoji)
    update_user_status.start()


bot.run(bot_config.discord_token)