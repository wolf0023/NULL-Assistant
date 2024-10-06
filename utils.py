import os
import json
from duckduckgo_search import AsyncDDGS
from constants import (
    log,
)

# threadが存在するか確認
async def is_thread_exist(thread_id: int) -> bool:
    file_path = os.path.join("data", f"{thread_id}.json")
    is_exist = os.path.exists(file_path)
    log.debug(f"スレッドが存在するか確認します:")
    log.debug(f"パス: {file_path}")
    log.debug(f"結果: {is_exist}")
    return is_exist

# threadの履歴の書き込み
async def store_thread_history(data: dict, thread_id: int) -> None:
    log.debug("スレッドを保存中...")

    # ディレクトリが存在しない場合はディレクトリを作成
    dir_path = os.path.join("data")
    os.makedirs(dir_path, exist_ok=True)

    # jsonファイルに書き込む
    file_path = os.path.join(dir_path, f"{thread_id}.json")
    try:
        with open(file_path, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log.exception(f"ファイルの書き込みに失敗しました:")
        log.error(f"オブジェクトの種類: {type(e)}")
        log.error(f"その他情報: {e}")

# threadの履歴の読み込み
async def load_thread_history(thread_id: int) -> dict:
    log.debug("スレッドを読み込み中...")
    # 履歴が存在しない場合はNoneを返す
    if not await is_thread_exist(thread_id):
        return None
    # jsonファイルを読み込む
    file_path = os.path.join("data", f"{thread_id}.json")
    try:
        with open(file_path, "r", encoding="UTF-8") as f:
            return json.load(f)
    except Exception as e:
        log.exception(f"ファイルの読み込みに失敗しました:")
        log.error(f"オブジェクトの種類: {type(e)}")
        log.error(f"その他情報: {e}")

# 保存形式に変換
async def convert_to_data(role: str, text: str) -> dict:
    data = {"role": role, "parts": [text,]}
    return data

# threadを削除
async def delete_thread(thread_id: int) -> None:
    log.info(f"{thread_id}を削除しました")
    # threadが存在するか確認し、存在する場合は削除
    if await is_thread_exist(thread_id):
        file_path = os.path.join("data", f"{thread_id}.json")
        try:
            os.remove(file_path)
        except Exception as e:
            log.exception(f"ファイルの削除に失敗しました:")
            log.error(f"オブジェクトの種類: {type(e)}")
            log.error(f"その他情報: {e}")

# 文末の改行と空白を削除
async def remove_line_breaks(text: str):
    if text[-1] == "\n" or text[-1] == " ":
        text = text[:-1]
        return await remove_line_breaks(text)
    else:
        return text

# コードブロックの空白や改行を削除、また、無駄な改行を削除
async def remove_unnecessary_line(text: str):
    text = text.replace("``` ", "```")
    text = text.replace("```\n\n", "```\n")
    text = text.replace("\n\n```", "\n```")
    text = text.replace("\n\n", "\n")
    return text

# DuckDuckGo検索
async def search_on_ddgs(word: str, max: int):
        try:
            results = await AsyncDDGS(proxy="None").atext(
                keywords=word,
                safesearch='moderate',
                region="jp-jp",
                backend='api',
                max_results=max,
            )
        except Exception as e:
            log.exception(f"検索エンジンでエラーが発生しました:")
            log.error(f"オブジェクトの種類: {type(e)}")
            log.error(f"その他情報: {e}")
            return None
        return results

# 送信者の名前を挿入
async def insert_user_name(user_name: str, user_input: str) -> str:
    return f"{user_name}: {user_input}"