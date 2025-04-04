import requests
import json
import base64
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# NEAR RPC API Endpoint
RPC_URL = "https://rpc.mainnet.near.org"
TOKEN_CONTRACT = "game.hot.tg"

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7417471699:AAGX0GwcVLJ4GAD1pucGMG4ZHDPeIZyC2SY"

# ✅ Whitelisted Users (Only these can use the bot)
WHITELISTED_USERS = [123456789, 987654321]  # Telegram User IDs

def get_token_decimals():
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": "dontcare",
            "method": "query",
            "params": {
                "request_type": "call_function",
                "finality": "final",
                "account_id": TOKEN_CONTRACT,
                "method_name": "ft_metadata",
                "args_base64": ""
            }
        }
        response = requests.post(RPC_URL, json=payload).json()
        raw_metadata = "".join(map(chr, response["result"]["result"]))
        metadata = json.loads(raw_metadata)
        return int(metadata.get("decimals", 18))
    except Exception as e:
        return 18

def get_token_balance(address, decimals):
    try:
        args = {"account_id": address}
        args_base64 = base64.b64encode(json.dumps(args).encode()).decode()
        payload = {
            "jsonrpc": "2.0",
            "id": "dontcare",
            "method": "query",
            "params": {
                "request_type": "call_function",
                "finality": "final",
                "account_id": TOKEN_CONTRACT,
                "method_name": "ft_balance_of",
                "args_base64": args_base64
            }
        }
        response = requests.post(RPC_URL, json=payload).json()
        raw_balance = "".join(map(chr, response["result"]["result"])).strip('"')
        return int(raw_balance) / (10**decimals)
    except:
        return 0.0

def check_balance(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in WHITELISTED_USERS:
        update.message.reply_text("🚫 You are not authorized to use this bot!")
        return

    if not context.args:
        update.message.reply_text("⚠️ Usage: /check <near_address>")
        return

    address = context.args[0]
    decimals = get_token_decimals()
    balance = get_token_balance(address, decimals)
    
    response = f"🔹 {address} Balance: {balance:.6f} HOT"
    update.message.reply_text(response)

# ✅ Telegram Bot Setup
updater = Updater(TELEGRAM_BOT_TOKEN)
updater.dispatcher.add_handler(CommandHandler("check", check_balance))

updater.start_polling()
updater.idle()
