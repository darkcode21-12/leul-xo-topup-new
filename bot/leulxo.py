from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler

BOT_TOKEN = "8210230571:AAE9X5qR8hP3z4vDTWwldHQp0_7c1eF6fGQ"
LEUL_CHAT_ID = 6718568837 # Admin (Leul) chat ID


orders = {}

user_steps = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == LEUL_CHAT_ID:
        await update.message.reply_text(
            "Welcome Leul! Use /pending to see all pending orders."
        )
    else:
        user_steps[user_id] = 'awaiting_screenshot'
        await update.message.reply_text(
            '''Welcome to Leul XO Bot!\nPlease send your payment screenshot to start your order. 🌟    ❗️❗️❗️❗️❗️🌟
         PAYMENT METHOD
TELLEBIRR🏦  
➡️ +251942695197
🟣 NAME-Tewodros'''
        )

# Handle screenshot
async def handle_user_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == LEUL_CHAT_ID:
        return  # ignore admin photos here

    step = user_steps.get(user_id)
    if step != 'awaiting_screenshot':
        await update.message.reply_text("Please follow the steps. You should send diamonds or UID next.")
        return

    file_id = update.message.photo[-1].file_id
    orders.setdefault(user_id, {})['screenshot_file_id'] = file_id
    orders[user_id]['status'] = 'pending'

    user_steps[user_id] = 'awaiting_diamond'

    # Send screenshot to admin
    await context.bot.send_photo(
        chat_id=LEUL_CHAT_ID,
        photo=file_id,
        caption=f"User ID {user_id} sent a payment screenshot."
    )

    await update.message.reply_text("Screenshot received! How many diamonds do you want?")

# Handle diamond input
async def handle_user_diamond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == LEUL_CHAT_ID:
        return

    step = user_steps.get(user_id)
    if step != 'awaiting_diamond':
        await update.message.reply_text("Please send the screenshot first.")
        return

    diamonds = update.message.text
    if not diamonds.isdigit():
        await update.message.reply_text("Please enter a valid number for diamonds.")
        return

    orders[user_id]['diamonds'] = int(diamonds)
    user_steps[user_id] = 'awaiting_uid'

    await update.message.reply_text("Diamonds recorded. Please enter your Free Fire UID.")

# Handle Free Fire UID
async def handle_user_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == LEUL_CHAT_ID:
        return

    step = user_steps.get(user_id)
    if step != 'awaiting_uid':
        await update.message.reply_text("Please follow the steps: screenshot → diamonds → UID.")
        return

    ff_uid = update.message.text
    orders[user_id]['ff_uid'] = ff_uid
    user_steps[user_id] = None  # completed steps

    # Notify admin
    await context.bot.send_message(
        chat_id=LEUL_CHAT_ID,
        text=(
            f"New order:\nUser ID: {user_id}\nDiamonds: {orders[user_id]['diamonds']}\n"
            f"Free Fire UID: {ff_uid}\nStatus: Pending.\nUse /deliver_{user_id} to send final screenshot."
        )
    )

    await update.message.reply_text("Your order has been recorded. Leul will notify you once it's completed ✅")

# ========== ADMIN HANDLERS ==========

# List pending orders
async def pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != LEUL_CHAT_ID:
        return

    pending = [uid for uid, o in orders.items() if o.get('status') == 'pending']
    if not pending:
        await update.message.reply_text("No pending orders.")
        return

    msg = "Pending Orders:\n"
    for uid in pending:
        o = orders[uid]
        msg += f"User ID: {uid} | Diamonds: {o['diamonds']} | UID: {o['ff_uid']}\n"
    await update.message.reply_text(msg)

# Deliver order (triggered via /deliver_userid command)
async def deliver_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != LEUL_CHAT_ID:
        return

    cmd = update.message.text
    if not cmd.startswith("/deliver_"):
        return

    try:
        target_user_id = int(cmd.split("_")[1])
    except:
        await update.message.reply_text("Invalid command format. Use /deliver_userid")
        return

    if target_user_id not in orders or orders[target_user_id]['status'] != 'pending':
        await update.message.reply_text("No pending order found for this user.")
        return

    # Set admin step
    context.user_data['current_delivery_user'] = target_user_id
    await update.message.reply_text(
        f"Please send the final delivery screenshot for User ID {target_user_id}."
    )

# Handle admin final screenshot
async def handle_admin_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != LEUL_CHAT_ID:
        return

    target_user_id = context.user_data.get('current_delivery_user')
    if not target_user_id or target_user_id not in orders:
        await update.message.reply_text("Use /deliver_userid to select which order to deliver.")
        return

    file_id = update.message.photo[-1].file_id
    # Send final screenshot to user
    await context.bot.send_photo(
        chat_id=target_user_id,
        photo=file_id,
        caption="Your order has been completed. Leul XO delivered successfully ✅"
    )

    orders[target_user_id]['status'] = 'completed'
    context.user_data['current_delivery_user'] = None

    await update.message.reply_text(f"Order delivered to User ID {target_user_id}.")

# ========== MAIN ==========

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.User(LEUL_CHAT_ID), handle_user_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.User(LEUL_CHAT_ID), handle_user_diamond))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.User(LEUL_CHAT_ID), handle_user_uid))

    # Admin handlers
    app.add_handler(CommandHandler("pending", pending_orders))
    app.add_handler(MessageHandler(filters.PHOTO & filters.User(LEUL_CHAT_ID), handle_admin_photo))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(LEUL_CHAT_ID), deliver_order))

    print("Bot is running...")
    app.run_polling()
