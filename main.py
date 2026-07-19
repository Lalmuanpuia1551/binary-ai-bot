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
        "You are a binary options trading bot. Analyze the chart screenshot.\n"
        "Respond ONLY with a JSON object containing 'direction' (BUY, SELL, or WAIT) and 'confidence' (0-100%).\n"
        "Example output: {\"direction\": \"BUY\", \"confidence\": \"85%\"}"
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
        
        raw_text = response.choices.message.content.strip()
        return json.loads(raw_text)
    except Exception as e:
        # Error text a thui luhei lova tawi tea siam nan
        return {"error": "AI Gateway timeout or invalid response"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📸 Upload Chart Guide")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        "👋 Fanaicharts QX Bot-ah lo hlawhtling takin lo lut rawh!\n\n"
        "⚠️ **THLALAK THAWN DAN TUR:**\n"
        "Chat chhutna zawn sir a **Paperclip icon 📎** kha hmet la, i 1-minute chart screenshot fiah tak kha va thawn (upload) tawp rawh le!",
        reply_markup=reply_markup
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 **Hriattirna:** Khawngaihin chat chhutna zawn sir a **Paperclip icon 📎** hmet khan i chart screenshot kha thlalak (Photo) angin rawn thawn zawk rawh le."
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

        # Key a lo chhiar dik loh thut pawha message lian duah lo lanna tur liahna
        direction = str(result.get('direction', 'WAIT')).upper()
        confidence = str(result.get('confidence', '70%'))

        # Safe response checking (Message is too long thup thakna)
        if "BUY" in direction:
            await update.message.reply_text(f"🟢 **NEXT CANDLE: BUY (CALL)**\n📈 **Confidence:** {confidence}\n🚀 *Signal her lut rawh!*")
        elif "SELL" in direction:
            await update.message.reply_text(f"🔴 **NEXT CANDLE: SELL (PUT)**\n📉 **Confidence:** {confidence}\n🔥 *Signal her lut rawh!*")
        else:
            await update.message.reply_text(f"⚪ **NO TRADE (WAIT)**\n⏳ **Confidence:** {confidence}\n💤 *Nghak deuh rih rawh.*")

    except Exception as e:
        await update.message.reply_text("❌ System Error: Please try again with a cleaner screenshot.")

def main():
    print("Bot is deploying final safe system...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
