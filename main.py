import os
import io
import base64
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from openai import OpenAI

# Environment Variables atanga chhiar tur
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# AICredits Gateway
ai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://aicredits.in"
)

def encode_image_bytes(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def analyze_chart_with_ai(image_bytes):
    base64_image = encode_image_bytes(image_bytes)
    
    prompt = (
        "You are a 60-second binary options scalper. "
        "Mentally analyze candlestick psychology, SnR, and indicators.\n"
        "Provide a strict response in this JSON format only:\n"
        "{\n"
        "  \"direction\": \"BUY or SELL or WAIT\",\n"
        "  \"confidence\": \"00%\"\n"
        "}"
    )

    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o",
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

# /start hmeh huna Upload Button rawn lanna tur
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Keyboard button mawi tak duanna
    keyboard = [[KeyboardButton("📸 Upload Chart")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        "👋 Fanaicharts QX Bot-ah hian lo hlawhtling takin lo lut rawh!\n\n"
        "A hnuaia button zawn khân hmet la, i 1-minute chart screenshot kha va thawn tawp rawh le.",
        reply_markup=reply_markup
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_message = await update.message.reply_text("🧠 Analyzing chart...")
    try:
        photo_file = await update.message.photo[-1].get_file()
        image_stream = io.BytesIO()
        await photo_file.download_to_memory(out=image_stream)
        image_bytes = image_stream.getvalue()

        result = analyze_chart_with_ai(image_bytes)
        
        await status_message.delete()

        if "error" in result:
            await update.message.reply_text(f"❌ API Error: {result['error']}")
            return

        direction = result['direction']
        confidence = result['confidence']

        # Message is too long error thup nan emoji chiang tak leh text tawi chauh kan hman tir ang
        if direction == "BUY":
            await update.message.reply_text(
                f"🟢 **NEXT CANDLE: BUY (CALL)**\n"
                f"📈 **Confidence:** {confidence}\n"
                f"🚀 *Signal her lut nghal rawh!*"
            )
        elif direction == "SELL":
            await update.message.reply_text(
                f"🔴 **NEXT CANDLE: SELL (PUT)**\n"
                f"📉 **Confidence:** {confidence}\n"
                f"🔥 *Signal her lut nghal rawh!*"
            )
        else:
            await update.message.reply_text(
                f"⚪ **NO TRADE (WAIT)**\n"
                f"⏳ **Confidence:** {confidence}\n"
                f"💤 *Market fiah rih lo, nghak deuh rawh.*"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ System Error: {str(e)}")

def main():
    print("Bot is updating with menu button...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
