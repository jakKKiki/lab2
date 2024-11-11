from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from pyngrok import ngrok

# 建立 Flask 應用程式
app = Flask(__name__)

# 設置你的 Channel Access Token 和 Channel Secret
CHANNEL_ACCESS_TOKEN = '你的 Channel Access Token'
CHANNEL_SECRET = '你的 Channel Secret'
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 設置 Webhook 處理函數
@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 HTTP 請求中的 X-Line-Signature 標頭
    signature = request.headers['X-Line-Signature']
    # 將請求內容轉為文本
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 驗證請求的合法性
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 設置接收訊息的事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 回覆相同的訊息
    message = TextSendMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run(port=5000)
