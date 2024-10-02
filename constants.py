import os
import dotenv
import logging
from rich.logging import RichHandler

#------ .env の読み込み ------
dotenv.load_dotenv()

#------ Rich logging ------
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        RichHandler(
            rich_tracebacks=True,
            show_path=False,
            tracebacks_word_wrap=False,
        )
    ]
)
log = logging.getLogger(__name__)

#------ Discord ------#
DISCORD_TOKEN_KEY = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

#------ Gemini ------#
MIN_MESSAGE_LENGTH = 1
MAX_MESSAGE_LENGTH = 1500
MAX_COUNTS = 50

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#------ Model Message ------#
ONLY_IN_TEXT_CHANNEL = 'このコマンドはテキストチャンネルでのみだ。'
ONLY_IN_THREAD_CHANNEL = 'このコマンドはスレッドチャンネルでのみだ。'
NEW_THREAD_CREATED = '新しくチャットが作成されたぞ！！'
THREAD_NOT_FOUND = 'スレッドが見つからないな...'
CONFIRM_TO_DELETE_THREAD = 'このスレッドはまもなくクローズされまーす。'
THREAD_DELETED = ':lock: このスレッドはクローズされたよ。'
TOO_MANY_MESSAGES = ':lock: これ以上は会話が続けられないみたいだな...'
MESSAGE_IS_EMPTY = 'ん？'
TOO_LONG_MESSAGE = 'あまり長いメッセージは読めないんだ...'
API_KEY_NOT_FOUND = 'うーん...何かがおかしいなぁ'
NOT_FOUND = 'ふむ...ちょっと考えがまとまらないなぁ'
RATE_LIMIT = 'おっと...ちょっと待っててくれないか？'
LOCKED_THREAD = 'ちょっと待ってくれ...'
ERROR = 'ごめん！ちょっと急用を思い出した！'
EXIT_BOT = 'んじゃあ、また呼んでくれよな！'