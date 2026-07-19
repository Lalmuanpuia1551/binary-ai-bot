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

# AICredits Gateway (Fiah taka her rem sa)
ai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://aicredits.in"
)

def encode_image_bytes(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def analyze_chart_with_ai(image_bytes):
    base64_image = encode_image_bytes(image_bytes)
    
    # Prompt tawi leh khauh, JSON chauh pe chhuak tura hrilhna
    prompt = (
        "You are a 60-second binary options scalper. Analyze this chart snapshot.\n"
        "Return ONLY a valid JSON object matching this structure exactly, with NO other text:\n"
        "{\n"
        "  \"direction\": \"BUY\",\n"
        "  \"confidence\": \"85%\"\n"
        "}\n"
        "The direction value must be either BUY, SELL, or WAIT."
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
        
        # Raw response lo in-print fiah hrim hrim nan
        raw_text = response.choices.message.content.strip()
        return json.loads(raw_text)
    except Exception as e:
        return {"error": str(e)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Keyboard button chiang tak dah nawn leh rih ila
    keyboard = [[KeyboardButton("📸 Upload Chart Guide")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        "👋 Fanaicharts QX Bot-ah lo hlawhtling takin lo lut rawh!\n\n"
        "⚠️ **THLALAK THAWN DAN TUR:**\n"
        "A hnuai a button khi hmet lovin, i chat chhutna sir a **Paperclip icon 📎 (Attachment)** emaw **Camera icon** kha hmet zawk la, i 1-minute chart screenshot fiah tak kha va thawn (upload) tawp rawh le!",
        reply_markup=reply_markup
    )

# Text satliah button a lo hmeh palha lo chhan dan tur
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if "Upload Chart" in user_text:
        await update.message.reply_text(
            "💡 **Hriattirna:** Khawngaihin a hnuai a button khi hmet lovin, chat chhutna zawn sir a **Paperclip icon 📎** hmet khan i chart screenshot kha thlalak (Photo) angin rawn thawn zawk rawh le."
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
            await update.message.reply_text(f"❌ API Error: {result['error']}\nCheck if your wallet has balance.")
            return

        # JSON key a rawn chhiar sual thut thil fiahna
        direction = result.get('direction', 'WAIT')
        confidence = result.get('confidence', '0%')

        # Error bo thak khawpa message tawi fel fiah si
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
    print("Bot is starting up with final updates...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
        
