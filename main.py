import discord
from discord import app_commands
import asyncio
import datetime

from utils import (
    is_thread_exist,
    store_thread_history,
    load_thread_history,
    convert_to_data,
    delete_thread,
    insert_user_name,
)
from constants import (
    log,
    DISCORD_TOKEN_KEY,
    DISCORD_GUILD_ID,
    MIN_MESSAGE_LENGTH,
    MAX_MESSAGE_LENGTH,
    MAX_COUNTS,
    ONLY_IN_TEXT_CHANNEL,
    ONLY_IN_THREAD_CHANNEL,
    NEW_THREAD_CREATED,
    THREAD_NOT_FOUND,
    CONFIRM_TO_DELETE_THREAD,
    THREAD_DELETED,
    TOO_MANY_MESSAGES,
    EXIT_BOT,
)
from generation import create_response

#------ 変数関連 ------
temporal_data = {}
locked_threads = []

#------ Discord Bot セットアップ ------
intents = discord.Intents.default()
intents.message_content = True
activity = discord.Game(name="chatting...")

client = discord.Client(intents=intents, activity=activity)
tree = app_commands.CommandTree(client=client)

# Discord Bot 開始時
@client.event
async def on_ready():
    try:
        tree.copy_global_to(guild=discord.Object(id=DISCORD_GUILD_ID))
        await tree.sync(guild=discord.Object(id=DISCORD_GUILD_ID))
        log.info(f"{client.user}としてログインしました。（ID: {client.user.id}）")
    except Exception as e:
        log.error(f"ログイン時にエラーが発生しました")
        log.error(f"種類: {type(e)}")
        log.error(f"{e}")

#------ Discord Bot Commands ------
@tree.command(name="help", description="ヘルプを表示します")
@app_commands.guild_only()
@app_commands.checks.cooldown(1, 1.0, key=None)
@app_commands.checks.has_permissions(view_channel=True)
@app_commands.checks.has_permissions(send_messages=True)
@app_commands.checks.bot_has_permissions(view_channel=True)
@app_commands.checks.bot_has_permissions(send_messages=True)
async def help_command(inter: discord.Interaction):
    # embedの作成
    embed_title = ":grey_question: **ヘルプ一覧**"
    embed_description = "\n".join(
        (
            "__**Bot紹介**__",
            "このBotは、スレッド内で、会話を行うことができます。",
            "",
            "__**使用できるコマンドは次のとおりです**__",
            "- **help** - このヘルプを表示します。",
            "- **create [<title>]** - チャットを作成します。タイトルはスレッド名です。",
            "- **close** - チャットを閉じます。スレッド内で実行する必要があります。",
            "- **end** - Botを終了します。",
        )
    )
    color = 0xffffff
    footer = "created by wolf0023"
    embed = discord.Embed(
        title=embed_title,
        description=embed_description,
        colour=color
    )
    embed.set_footer(text=footer)

    await inter.response.send_message(embed=embed)

@help_command.error
async def help_command_error(error):
    await handle_slash_command_error(error)

@tree.command(name="create", description="新しいチャットを作成します")
@app_commands.guild_only()
@app_commands.checks.cooldown(1, 3.0, key=None)
@app_commands.checks.has_permissions(view_channel=True)
@app_commands.checks.has_permissions(send_messages=True)
@app_commands.checks.has_permissions(create_private_threads=True)
@app_commands.checks.has_permissions(manage_threads=True)
@app_commands.checks.bot_has_permissions(view_channel=True)
@app_commands.checks.bot_has_permissions(send_messages=True)
@app_commands.checks.bot_has_permissions(create_private_threads=True)
@app_commands.checks.bot_has_permissions(manage_threads=True)
@app_commands.describe(title="タイトル")
async def create_command(inter: discord.Interaction, title: str = "新しいチャット"):
    # Text channel のみ
    if not isinstance(inter.channel, discord.TextChannel):
        await inter.response.send_message(ONLY_IN_TEXT_CHANNEL, ephemeral=True)
        return
    
    # threadの作成
    thread_history = {
        "title": title,
        "count": 0,
        "messages": [],
    }
    thread = await inter.channel.create_thread(
        name=title,
        auto_archive_duration=1440,
        slowmode_delay=1,
        type=discord.ChannelType.public_thread,
    )
    await store_thread_history(data=thread_history, thread_id=thread.id)

    # 作成日時を取得
    jst = datetime.timezone(datetime.timedelta(hours=9))
    creation_date = thread.created_at.astimezone(tz=jst).strftime("%Y/%m/%d %H:%M")

    # embedの作成
    embed_title = NEW_THREAD_CREATED
    embed_description = "\n".join(
        (
            f"__**チャット情報**__",
            f"- **タイトル** : `{title}`",
            f"- **作成者** : `{inter.user.name}`",
            f"- **作成日時** : `{creation_date}`",
            f"__**サーバー情報**__",
            f"- **鯖名** : `{inter.guild.name}`",
            f"- **スレッドID** : `{thread.id}`",
        )
    )
    color = 0xffffff
    link_to_thread = f"https://discord.com/channels/{inter.guild.id}/{thread.id}"
    embed = discord.Embed(
        title=embed_title,
        description=embed_description,
        colour=color,
        url=link_to_thread,
    )

    await inter.response.send_message(embed=embed)
    log.info(f"{inter.user.name}が新しいチャットを作成しました: {title}")

@create_command.error
async def create_command_error(error):
    await handle_slash_command_error(error)


@tree.command(name="close", description="チャットを閉じます")
@app_commands.guild_only()
@app_commands.checks.has_permissions(view_channel=True)
@app_commands.checks.bot_has_permissions(view_channel=True)
@app_commands.checks.bot_has_permissions(send_messages=True)
@app_commands.checks.bot_has_permissions(manage_threads=True)
async def close_command(inter: discord.Interaction):
    # Thread channel のみ
    if not isinstance(inter.channel, discord.Thread):
        await inter.response.send_message(ONLY_IN_THREAD_CHANNEL, ephemeral=True)
        return

    # threadが存在しているか確認
    thread = inter.channel
    if not await is_thread_exist(thread.id):
        await inter.response.send_message(THREAD_NOT_FOUND, ephemeral=True)
        return
    
    # threadのクローズメッセージの送信
    await inter.response.send_message(CONFIRM_TO_DELETE_THREAD, ephemeral=True)
    await asyncio.sleep(1)

    # threadをクローズ
    await thread.send(THREAD_DELETED)
    await thread.edit(archived=True, locked=True)
    await delete_thread(thread.id)

@close_command.error
async def close_command_error(error):
    await handle_slash_command_error(error)


@tree.command(name="end", description="Botを正常に終了します")
@app_commands.guild_only()
@app_commands.checks.cooldown(1, 5.0, key=None)
@app_commands.checks.has_permissions(administrator=True)
async def end_command(inter: discord.Interaction):
    # Text channel のみ
    if not isinstance(inter.channel, discord.TextChannel):
            await inter.response.send_message(ONLY_IN_TEXT_CHANNEL, ephemeral=True)
            return
    
    try:
        # 終了
        log.info(f"{inter.user.name}が終了コマンドを実行しました")
        await inter.response.send_message(EXIT_BOT, ephemeral=True)
        await client.close()
    except Exception as e:
        log.error(f"Bot終了中にエラーが発生しました")
        log.error(f"種類: {type(e)}")
        log.error(f"{e}")

@end_command.error
async def end_command_error(error):
    await handle_slash_command_error(error)


#------ 関数関連 ------
# スラッシュコマンドのエラー処理
async def handle_slash_command_error(error: Exception):
    match error:
        case app_commands.errors.BotMissingPermissions():
            return "Botに必要な権限が足りていません。"
        case app_commands.errors.MissingPermissions():
            return "このコマンドを実行する権限がありません。"
        case app_commands.errors.CommandOnCooldown():
            return "クールダウン中です。少し待ってから再度実行してください。"
        case _:
            log.error(f"エラーが発生しました: {error}")
            return "エラーが発生しました。"

# メッセージの送信
async def send_message(message: discord.Message):
    user_input = message.content
    user_name = message.author.name
    user_message = await insert_user_name(user_name, user_input)
    thread_id = message.channel.id
    is_error = False

    # ロック時の処理
    if thread_id in locked_threads:
        message_length = len(user_input)
        if message_length < MIN_MESSAGE_LENGTH or message_length > MAX_MESSAGE_LENGTH:
            return
        await store_temporal_message(thread_id, user_message)
    
    # ロックされていない場合
    await append_id(thread_id) # ロック
    async with message.channel.typing():
        thread_history = await load_thread_history(thread_id)
        response, gemini_output, is_error = await create_response(
            user_input=user_input,
            history=thread_history["messages"],
            user_name=user_name,
            counts=thread_history["count"],
        )
    await message.channel.send(response)

    if not is_error:
        thread_history["count"] += 1
        # 入力の保存
        data = await convert_to_data("user", user_message)
        thread_history["messages"].append(data)
        # 一時的なデータを保存
        for data in temporal_data[thread_id]:
            thread_history["messages"].append(data)
        # 出力の保存
        data = await convert_to_data("model", gemini_output)
        thread_history["messages"].append(data)
        await store_thread_history(data=thread_history, thread_id=thread_id)
        
    
    # 一時履歴の削除
    await delete_temporal_data(thread_id)
    await remove_id(thread_id) # ロック解除

    # 最大回数に達した場合、スレッドをクローズする
    if thread_history["count"] >= MAX_COUNTS:
        await message.channel.send(TOO_MANY_MESSAGES)
        await delete_thread(thread_id)


# ロックされたスレッドのIDを追加
async def append_id(thread_id: int):
    global locked_threads, temporal_data
    if thread_id not in locked_threads:
        locked_threads.append(thread_id)
        temporal_data[thread_id] = []

# ロックされたスレッドのIDを削除
async def remove_id(thread_id: int):
    global locked_threads
    if thread_id in locked_threads:
        locked_threads.remove(thread_id)

# 一時的に保存
async def store_temporal_message(thread_id: int, user_message: str):
    global temporal_data
    if thread_id in locked_threads:
        temporal_data[thread_id].append({"role": "user", "content": user_message}) 

# 一時的なデータを削除
async def delete_temporal_data(thread_id: int):
    global temporal_data
    if thread_id in locked_threads:
        del temporal_data[thread_id]

#------ イベント関連 ------
@client.event
async def on_message(message: discord.Message):
    # Botのメッセージは無視
    if message.author == client.user:
        return
    
    # DMの場合は無視
    if message.guild is None:
        return
    
    # 別のスレッドは無視
    thread = message.channel
    if not await is_thread_exist(thread.id):
        return
    
    # メッセージの送信
    await send_message(message)

#------ Botの起動 ------
client.run(DISCORD_TOKEN_KEY)