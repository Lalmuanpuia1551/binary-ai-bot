import os
import io
import base64
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Render Environment Variables atanga chhiar tur
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# AICredits hman nan base_url her rem a ngai (He lai hi a pawimawh ber)
ai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://aicredits.in"
)

def encode_image_bytes(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def analyze_chart_with_ai(image_bytes):
    base64_image = encode_image_bytes(image_bytes)
    
    prompt = (
        "You are a 60-second binary options high-speed trading engine. "
        "Analyze this chart snapshot mentally for candlestick psychology, SnR, and indicators.\n"
        "Provide a strict response in this JSON format only:\n"
        "{\n"
        "  \"direction\": \"BUY or SELL or WAIT\",\n"
        "  \"confidence\": \"00%\"\n"
        "}"
    )

    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o",  # AICredits-ah pawh gpt-4o a hman tlang theih
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices.message.content)
    except Exception as e:
        return {"error": str(e)}

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_message = await update.message.reply_text("🧠 Analyzing chart...")
    try:
        photo_file = await update.message.photo[-1].get_file()
        image_stream = io.BytesIO()
        await photo_file.download_to_memory(out=image_stream)
        image_bytes = image_stream.getvalue()

        result = analyze_chart_with_ai(image_bytes)
        
        # 'Analyzing...' status message hmet hlum rawh se
        await status_message.delete()

        if "error" in result:
            await update.message.reply_text(f"❌ API Error: {result['error']}\nCheck if your AICredits wallet has balance.")
            return

        direction = result['direction']
        confidence = result['confidence']

        # Animated Emoji Sticker leh prediction thawn chhuah dan tur
        if direction == "BUY":
            await update.message.reply_sticker("CAACAgIAAxkBAAEExbhmX62vAAEg4XyP_9l13_S8mB6D6wACFwADUr6DE6Fp-H-T0oVyNQQ")
            await update.message.reply_text(f"🟢 **NEXT CANDLE: BUY (CALL)**\n⚡ Confidence: {confidence}", parse_mode="Markdown")
        elif direction == "SELL":
            await update.message.reply_sticker("CAACAgIAAxkBAAEExbpmX63BAAEgAnj7q7vH7l4S0Wk89gACGQADUr6DEzK6Sg7bL7GfNQQ")
            await update.message.reply_text(f"🔴 **NEXT CANDLE: SELL (PUT)**\n⚡ Confidence: {confidence}", parse_mode="Markdown")
        else:
            await update.message.reply_sticker("CAACAgIAAxkBAAEExbxmX63TAAEgAdHq7vH7l4S0Wk89gACHQADUr6DEzK6Sg7bL7GfNQQ")
            await update.message.reply_text(f"⚪ **NO TRADE (WAIT)**\n⚡ Confidence: {confidence}", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Server Error: {str(e)}")

def main():
    print("Bot is up and running via AICredits Gateway...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
  
