from constants import (
    log,
    DISCORD_TOKEN_KEY
)
import discord
from discord import app_commands

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client=client)

@client.event
async def on_ready():
    try:
        tree.clear_commands(guild=None)
        await tree.sync(guild=None)
        log.info("コマンドをリセットしました。botを再度入れなおしてください。")
    except Exception as e:
        log.error(f"コマンドのリセットに失敗しました:")
        log.error(f"種類: {type(e)}")
        log.error(f"{e}")

client.run(DISCORD_TOKEN_KEY)