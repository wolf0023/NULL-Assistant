import asyncio
import google.generativeai as genai
import google.api_core.exceptions as api_core_except
import google.auth.exceptions as auth_except
from utils import (
    remove_line_breaks,
    remove_unnecessary_line,
    search_on_ddgs,
    insert_user_name,
)
from model import (
    MODEL_NAME,
    GENERATION_CONFIG,
    SAFETY_SETTINGS,
    system_instruction_NULL,
    system_instruction_SearchBot,
)
from constants import (
    log,
    MIN_MESSAGE_LENGTH,
    MAX_MESSAGE_LENGTH,
    MAX_COUNTS,
    GEMINI_API_KEY,
    MESSAGE_IS_EMPTY,
    TOO_LONG_MESSAGE,
    API_KEY_NOT_FOUND,
    NOT_FOUND,
    RATE_LIMIT,
    ERROR,
)

#------ Gemini Settings ------
genai.configure(api_key=GEMINI_API_KEY)

# メッセージの生成
class Model():
    def __init__(self, model: str, tools: str):
        if tools == "code_execution":
            self.model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                safety_settings=SAFETY_SETTINGS,
                system_instruction=model,
                tools=tools,
            )
        else:
            self.model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                safety_settings=SAFETY_SETTINGS,
                system_instruction=model,
            )
    async def generate_message(self, user_input: str, history: list):
        response = ""
        is_error = False
        try:
            # 履歴を読み込む
            gemini_session = self.model.start_chat(history=history)

            # トークン数の表示
            model_count_tokens = str(self.model.count_tokens(user_input)).replace("\n", " ")
            log.debug(f"トークン数: {model_count_tokens} from google.generativeai")

            # APIリクエストを送信
            response = await gemini_session.send_message_async(user_input)

            # レスポンスを取得
            response = response.text
        except genai.types.generation_types.StopCandidateException as e:
            # 再度リクエストを送信
            log.warning("生成が中断されたため、再度リクエストを送信します")
            log.warning(f"{e}")
            await asyncio.sleep(2)
            return await self.generate_message(user_input, history)
        except Exception as e:
            # エラー処理
            is_error = True
            response = await handle_gemini_error(e)
        
        return response, is_error
    
# メッセージの作成
async def create_response(
        user_input: str,
        history: list,
        user_name: str,
        counts: int,
) -> tuple[str, str, bool]:
    message = await insert_user_name(user_input, user_name)
    user_input_length = len(user_input)
    is_error = False
    model_NULL = Model(system_instruction_NULL, "code_execution")
    model_Search = Model(system_instruction_SearchBot, "")

    # メッセージの長さチェック
    if user_input_length < MIN_MESSAGE_LENGTH or user_input.isspace():
        is_error = True
        return MESSAGE_IS_EMPTY, "", is_error
    if user_input_length > MAX_MESSAGE_LENGTH:
        is_error = True
        return TOO_LONG_MESSAGE, "", is_error
    
    # 検索が必要な場合
    log.debug(f"DDGSに送信するメッセージ: {user_input}")
    word, is_error = await model_Search.generate_message(user_input=user_input, history=[])
    if not word.isspace() and not is_error:
        search_result = await search_on_ddgs(word, 5)
        message = user_input + "\n\n以下、ユーザーの入力ではない。\n## Webからの情報(必要に応じて参考にすること)\n"
        # 検索結果をメッセージに挿入
        for i, body in enumerate(search_result):
            message += f"{i}. " + body["body"] + "\n"
        log.debug(message)
    
    # 回答を生成する
    log.debug(f"NULLに送信するメッセージ: {user_input}")
    gemini_output, is_error = await model_NULL.generate_message(user_input=message, history=history)

    # 文の修正
    gemini_output = await remove_line_breaks(gemini_output)
    gemini_output = await remove_unnecessary_line(gemini_output)

    # メッセージの送信(Discordメッセージの最大文字数(2000)を超えないようにする)
    # MAX_COUNTSの2/3以上の回数の場合、色を変更
    icon = ":small_blue_diamond:" if counts < MAX_COUNTS*2//3 else ":small_orange_diamond:"
    send_text = gemini_output[:1500] + f"\n-# {icon}{counts+1}/{MAX_COUNTS}\n"

    log.debug("今行われた会話の内容:")
    log.debug(f"User: {user_input}")
    log.debug(f"Model: {gemini_output}")

    # タイピング速度
    gemini_output_length = len(gemini_output)
    await asyncio.sleep(gemini_output_length//100)

    return send_text, gemini_output, is_error

# geminiのエラー処理
async def handle_gemini_error(error: Exception):
    match error:
        case auth_except.DefaultCredentialsError():
            log.error("API キーに必要な権限がありません\n(google.auth.exceptions.DefaultCredentialsError)")
            return API_KEY_NOT_FOUND
        case api_core_except.NotFound():
            log.error("リクエストされたリソースが見つかりませんでした\n(google.api_core.exceptions.NotFound)")
            return NOT_FOUND
        case api_core_except.ResourceExhausted():
            log.error("レート制限を超えました\n(google.api_core.exceptions.ResourceExhausted)" )
            return RATE_LIMIT
        case _:
            log.error(f"想定外のエラーが発生しました" )
            log.error(f"種類: {type(error)}")
            log.error(f"{error}")
            return ERROR