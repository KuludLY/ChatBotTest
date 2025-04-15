import logging
import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
    ConversationHandler
)
import cohere

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Cohere client with your API key
cohere_client = cohere.Client('iYeX9ObubpQonU4jnTjcyIqRg12MlvSNeLkQi6bE')

# User data file
USER_DATA_FILE = 'user_data.json'

# Conversation states
SELECTING_LANGUAGE, SELECTING_QUIZ_DIFFICULTY, CHATTING = range(3)

# Language options
LANGUAGES = {
    "🇦🇪 Arabic": "Arabic",
    "🇪🇸 Spanish": "Spanish",
    "🇫🇷 French": "French",
    "🇩🇪 German": "German",
    "🇨🇳 Chinese": "Chinese",
    "🇯🇵 Japanese": "Japanese",
    "🇷🇺 Russian": "Russian"
}

# Quiz difficulties
QUIZ_DIFFICULTIES = {
    "🍏 Beginner": "easy",
    "🍎 Intermediate": "medium",
    "🌶️ Advanced": "hard"
}

# Main menu
MENU_KEYBOARD = [
    ["📝 Summarize", "🔍 Define Words"],
    ["🌍 Translate", "❓ Generate Quiz"],
    ["💬 Chat Mode", "⚙️ Settings"],
    ["ℹ️ Help"]
]

# Settings menu
SETTINGS_KEYBOARD = [
    ["🌐 Set Language", "📊 Set Quiz Difficulty"],
    ["🔙 Main Menu"]
]

# Chat mode keyboard
CHAT_KEYBOARD = [
    ["🔙 Exit Chat"]
]

# Load user data
def load_user_data():
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r') as f:
                data = json.load(f)
                # Ensure all existing entries have required keys
                for user_id, user_data in data.items():
                    if 'prefs' not in user_data:
                        user_data['prefs'] = {
                            'language': "Arabic",
                            'quiz_difficulty': "medium"
                        }
                    if 'chat_history' not in user_data:
                        user_data['chat_history'] = []
                return data
        return {}
    except Exception as e:
        logger.error(f"Error loading user data: {e}")
        return {}

# Save user data
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

# Get user data with defaults
def get_user_data(user_id):
    data = load_user_data()
    user_data = data.get(str(user_id), {})
    
    # Initialize if new user
    if not user_data:
        user_data = {
            'prefs': {
                'language': "Arabic",
                'quiz_difficulty': "medium"
            },
            'chat_history': []
        }
        data[str(user_id)] = user_data
        save_user_data(data)
    
    return user_data

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "📚 *Study Assistant Bot*\n\n"
        "Choose an action from the menu below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🆘 *How to use:*\n\n"
        "1. Send any text (paragraph, notes, etc.)\n"
        "2. Choose an action:\n"
        "- 📝 *Summarize*: Get a concise summary\n"
        "- 🔍 *Define Words*: Auto-detect hard words\n"
        "- 🌍 *Translate*: Convert to selected language\n"
        "- ❓ *Generate Quiz*: Create practice questions\n"
        "- 💬 *Chat Mode*: Have a conversation about your study topics\n"
        "- ⚙️ *Settings*: Change default language/quiz difficulty\n\n"
        "No commands needed – just use the buttons!",
        parse_mode="Markdown"
    )

# Settings menu
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = get_user_data(update.effective_user.id)
    await update.message.reply_text(
        f"⚙️ *Current Settings*\n\n"
        f"🌐 Language: {user_data['prefs']['language']}\n"
        f"📊 Quiz Difficulty: {user_data['prefs']['quiz_difficulty'].capitalize()}\n\n"
        "Select an option to change:",
        reply_markup=ReplyKeyboardMarkup(SETTINGS_KEYBOARD, resize_keyboard=True),
        parse_mode="Markdown"
    )

# Language selection
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language_options = [[lang] for lang in LANGUAGES.keys()]
    language_options.append(["🔙 Cancel"])
    await update.message.reply_text(
        "Select your preferred translation language:",
        reply_markup=ReplyKeyboardMarkup(language_options, resize_keyboard=True)
    )
    return SELECTING_LANGUAGE

# Save language preference
async def save_language(update: Update, context: CallbackContext):
    user_choice = update.message.text
    if user_choice == "🔙 Cancel":
        await settings(update, context)
        return ConversationHandler.END
    
    if user_choice in LANGUAGES:
        user_id = str(update.effective_user.id)
        data = load_user_data()
        user_data = data.get(user_id, {})
        if 'prefs' not in user_data:
            user_data['prefs'] = {}
        user_data['prefs']['language'] = LANGUAGES[user_choice]
        data[user_id] = user_data
        save_user_data(data)
        
        await update.message.reply_text(
            f"✅ Default language set to: {LANGUAGES[user_choice]}",
            reply_markup=ReplyKeyboardMarkup(SETTINGS_KEYBOARD, resize_keyboard=True)
        )
    else:
        await update.message.reply_text("Invalid selection. Please try again.")
    
    return ConversationHandler.END

# Quiz difficulty selection
async def set_quiz_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    difficulty_options = [[diff] for diff in QUIZ_DIFFICULTIES.keys()]
    difficulty_options.append(["🔙 Cancel"])
    await update.message.reply_text(
        "Select quiz difficulty level:",
        reply_markup=ReplyKeyboardMarkup(difficulty_options, resize_keyboard=True)
    )
    return SELECTING_QUIZ_DIFFICULTY

# Save quiz difficulty preference
async def save_quiz_difficulty(update: Update, context: CallbackContext):
    user_choice = update.message.text
    if user_choice == "🔙 Cancel":
        await settings(update, context)
        return ConversationHandler.END
    
    if user_choice in QUIZ_DIFFICULTIES:
        user_id = str(update.effective_user.id)
        data = load_user_data()
        user_data = data.get(user_id, {})
        if 'prefs' not in user_data:
            user_data['prefs'] = {}
        user_data['prefs']['quiz_difficulty'] = QUIZ_DIFFICULTIES[user_choice]
        data[user_id] = user_data
        save_user_data(data)
        
        await update.message.reply_text(
            f"✅ Quiz difficulty set to: {user_choice.replace('🍏', '').replace('🍎', '').replace('🌶️', '').strip()}",
            reply_markup=ReplyKeyboardMarkup(SETTINGS_KEYBOARD, resize_keyboard=True)
        )
    else:
        await update.message.reply_text("Invalid selection. Please try again.")
    
    return ConversationHandler.END

# Start chat mode
async def start_chat(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = load_user_data()
    user_data = data.get(str(user_id), {})
    
    # Clear previous chat history
    user_data['chat_history'] = []
    data[str(user_id)] = user_data
    save_user_data(data)
    
    await update.message.reply_text(
        "💬 *Chat Mode Activated*\n\n"
        "You can now chat with me about any study topic. "
        "I'll remember our conversation and provide helpful responses.\n\n"
        "Type '🔙 Exit Chat' to return to the main menu.",
        reply_markup=ReplyKeyboardMarkup(CHAT_KEYBOARD, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return CHATTING

# Handle chat messages
async def handle_chat_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_text = update.message.text
    data = load_user_data()
    user_data = data.get(str(user_id), {})
    
    if user_text == "🔙 Exit Chat":
        await start(update, context)
        return ConversationHandler.END
    
    # Add user message to chat history
    if 'chat_history' not in user_data:
        user_data['chat_history'] = []
    user_data['chat_history'].append({"role": "USER", "message": user_text})
    data[str(user_id)] = user_data
    save_user_data(data)
    
    try:
        # Generate response using Cohere's chat API
        response = cohere_client.chat(
            message=user_text,
            model="command",
            chat_history=user_data.get('chat_history', []),
            temperature=0.7
        )
        
        bot_response = response.text
        
        # Add bot response to chat history
        user_data['chat_history'].append({"role": "CHATBOT", "message": bot_response})
        data[str(user_id)] = user_data
        save_user_data(data)
        
        await update.message.reply_text(
            f"{bot_response}",
            reply_markup=ReplyKeyboardMarkup(CHAT_KEYBOARD, resize_keyboard=True),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        await update.message.reply_text(
            "❌ Sorry, I encountered an error. Please try again.",
            reply_markup=ReplyKeyboardMarkup(CHAT_KEYBOARD, resize_keyboard=True)
        )
    
    return CHATTING

# Summarize text
async def summarize_text(text: str) -> str:
    try:
        response = cohere_client.generate(
            model='command',
            prompt=f"Summarize this in 1-2 sentences:\n\n{text}",
            max_tokens=100,
            temperature=0.5
        )
        return response.generations[0].text.strip()
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return "❌ Could not summarize. Try shorter text."

# Define difficult words
async def define_words(text: str) -> str:
    try:
        word_response = cohere_client.generate(
            model='command',
            prompt=f"List 3-5 complex words in this text (comma-separated):\n\n{text}",
            max_tokens=50,
            temperature=0.3
        )
        words = [w.strip() for w in word_response.generations[0].text.split(",") if w.strip()][:5]

        definitions = []
        for word in words:
            def_response = cohere_client.generate(
                model='command',
                prompt=f"Define '{word}' in simple terms:",
                max_tokens=30,
                temperature=0.3
            )
            definitions.append(f"• *{word}*: {def_response.generations[0].text.strip()}")

        return "\n".join(definitions) if definitions else "No complex words found."
    except Exception as e:
        logger.error(f"Definition error: {e}")
        return "❌ Failed to define words."

# Translate text
async def translate_text(text: str, target_language: str) -> str:
    try:
        response = cohere_client.generate(
            model='command',
            prompt=f"Translate this to {target_language}:\n\n{text}",
            max_tokens=200,
            temperature=0.5
        )
        return response.generations[0].text.strip()
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return f"❌ Failed to translate to {target_language}."

# Generate quiz questions
async def generate_quiz(text: str, difficulty: str) -> str:
    try:
        prompt = f"Generate 3 {difficulty} difficulty quiz questions (with answers) about this text:\n\n{text}"
        if difficulty == "easy":
            prompt += "\n\nMake questions simple with direct answers."
        elif difficulty == "hard":
            prompt += "\n\nMake questions challenging with critical thinking required."

        response = cohere_client.generate(
            model='command',
            prompt=prompt,
            max_tokens=200,
            temperature=0.7
        )
        return response.generations[0].text.strip()
    except Exception as e:
        logger.error(f"Quiz error: {e}")
        return "❌ Could not generate quiz."

# Handle user messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text
    chat_data = context.chat_data
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    # Main menu actions
    if user_text in ["📝 Summarize", "🔍 Define Words", "🌍 Translate", "❓ Generate Quiz", "💬 Chat Mode", "⚙️ Settings", "ℹ️ Help"]:
        if user_text == "ℹ️ Help":
            await help_command(update, context)
        elif user_text == "⚙️ Settings":
            await settings(update, context)
        elif user_text == "💬 Chat Mode":
            return await start_chat(update, context)
        else:
            chat_data["action"] = user_text
            if user_text == "🌍 Translate":
                await update.message.reply_text(
                    f"Selected: {user_text}\nCurrent language: {user_data['prefs']['language']}\nSend me the text to translate!",
                    reply_markup=ReplyKeyboardMarkup([["🔙 Main Menu"]], resize_keyboard=True)
                )
            elif user_text == "❓ Generate Quiz":
                await update.message.reply_text(
                    f"Selected: {user_text}\nCurrent difficulty: {user_data['prefs']['quiz_difficulty']}\nSend me the text for quiz questions!",
                    reply_markup=ReplyKeyboardMarkup([["🔙 Main Menu"]], resize_keyboard=True)
                )
            else:
                await update.message.reply_text(
                    f"Selected: {user_text}\nNow send me the text!",
                    reply_markup=ReplyKeyboardMarkup([["🔙 Main Menu"]], resize_keyboard=True)
                )
        return

    # Return to main menu
    if user_text == "🔙 Main Menu":
        await start(update, context)
        return

    # Process text based on selected action
    if "action" in chat_data:
        action = chat_data["action"]
        await update.message.reply_chat_action("typing")

        if action == "📝 Summarize":
            result = await summarize_text(user_text)
            await update.message.reply_text(f"📌 *Summary:*\n\n{result}", parse_mode="Markdown")
        elif action == "🔍 Define Words":
            result = await define_words(user_text)
            await update.message.reply_text(f"📖 *Definitions:*\n\n{result}", parse_mode="Markdown")
        elif action == "🌍 Translate":
            result = await translate_text(user_text, user_data['prefs']['language'])
            await update.message.reply_text(f"🌐 *Translation ({user_data['prefs']['language']}):*\n\n{result}", parse_mode="Markdown")
        elif action == "❓ Generate Quiz":
            result = await generate_quiz(user_text, user_data['prefs']['quiz_difficulty'])
            await update.message.reply_text(f"🧠 *Quiz Questions ({user_data['prefs']['quiz_difficulty']}):*\n\n{result}", parse_mode="Markdown")

        del chat_data["action"]
    else:
        await update.message.reply_text(
            "Please select an action from the menu first!",
            reply_markup=ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
        )

# Cancel handler
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Operation cancelled.",
        reply_markup=ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    )
    return ConversationHandler.END

# Run the bot
def main():
    # Initialize user data file if it doesn't exist
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump({}, f)

    # Build the bot with your Telegram token
    application = ApplicationBuilder().token('7259831858:AAHN3HmrOFj7ELSx6ozwIfrQWX5Rov-SjU0').build()

    # Conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🌐 Set Language$"), set_language),
            MessageHandler(filters.Regex("^📊 Set Quiz Difficulty$"), set_quiz_difficulty),
            MessageHandler(filters.Regex("^💬 Chat Mode$"), start_chat)
        ],
        states={
            SELECTING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_language)],
            SELECTING_QUIZ_DIFFICULTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_quiz_difficulty)],
            CHATTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()