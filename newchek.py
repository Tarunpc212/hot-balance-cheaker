import requests
import json
import base64
import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
import os

# Logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# NEAR RPC API Endpoint
RPC_URL = "https://rpc.mainnet.near.org"
# HOT Token Contract Address
TOKEN_CONTRACT = "game.hot.tg"

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

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
        if "result" in response and "result" in response["result"]:
            raw_metadata = "".join(map(chr, response["result"]["result"]))
            metadata = json.loads(raw_metadata)
            return int(metadata.get("decimals", 18))
    except Exception as e:
        logging.error(f"Error fetching token decimals: {str(e)}")
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
        if "error" in response:
            return 0.0
        if "result" in response and "result" in response["result"]:
            raw_balance = "".join(map(chr, response["result"]["result"])).strip('"')
            return int(raw_balance) / (10**decimals)
    except Exception as e:
        logging.error(f"Error fetching balance for {address}: {str(e)}")
    return 0.0

def check_balance(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("❌ Please provide a valid address. Example: /check address.tg")
        return
    
    address = context.args[0]
    token_decimals = get_token_decimals()
    balance = get_token_balance(address, token_decimals)
    
    response_message = f"🔹 {address}: {balance:.6f} HOT"
    update.message.reply_text(response_message)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Bot is Active! Send /check <address> to get balances.")

def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    updater = Updater(bot.token, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("check", check_balance))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
