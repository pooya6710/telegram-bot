from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
import logging
import json
import nest_asyncio
from jdatetime import date as JalaliDate

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store student data
students = {}

# Dictionary to store weekly menu
menu_data = {
    "saturday": {"breakfast": "تخم مرغ", "lunch": "چلوکباب", "dinner": "سوپ"},
    "sunday": {"breakfast": "پنیر و گردو", "lunch": "خورشت قورمه سبزی", "dinner": "ماکارونی"},
    "monday": {"breakfast": "املت", "lunch": "چلو مرغ", "dinner": "کتلت"},
    "tuesday": {"breakfast": "عدسی", "lunch": "خورشت قیمه", "dinner": "کوکو سبزی"},
    "wednesday": {"breakfast": "کره و مربا", "lunch": "آبگوشت", "dinner": "پیتزا"},
    "thursday": {"breakfast": "نان و پنیر", "lunch": "چلو ماهی", "dinner": "سوپ"},
    "friday": {"breakfast": "حلوا ارده", "lunch": "خورشت فسنجان", "dinner": "ساندویچ"}
}

# File to store reservations
RESERVATION_FILE = "reservations.json"

# Update the load_reservations function to handle empty or invalid JSON files
def load_reservations():
    try:
        with open(RESERVATION_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return an empty dictionary if the file is missing or invalid
        return {}

# Update the save_reservations function to store Persian day and meal names in the JSON file
persian_days = {
    "saturday": "شنبه",
    "sunday": "یکشنبه",
    "monday": "دوشنبه",
    "tuesday": "سه‌شنبه",
    "wednesday": "چهارشنبه",
    "thursday": "پنج‌شنبه",
    "friday": "جمعه"
}

persian_meals = {
    "breakfast": "صبحانه",
    "lunch": "ناهار",
    "dinner": "شام"
}

# Ensure reservations persist across restarts by saving them on every update
def save_reservations(reservations):
    # Convert English keys to Persian before saving
    persian_reservations = {}
    for feeding_code, days in reservations.items():
        persian_days_data = {}
        for day, meals in days.items():
            persian_day = persian_days.get(day, day)
            persian_meals_data = {persian_meals.get(meal, meal): name for meal, name in meals.items()}
            persian_days_data[persian_day] = persian_meals_data
        persian_reservations[feeding_code] = persian_days_data

    with open(RESERVATION_FILE, "w", encoding="utf-8") as file:
        json.dump(persian_reservations, file, ensure_ascii=False, indent=4)

# Initialize reservations
reservations = load_reservations()

# Add a list of owner chat IDs
OWNER_CHAT_IDS = ["286420965"]  # Replace YOUR_CHAT_ID with the provided chat ID

# Function to check if a user is an owner
def is_owner(chat_id):
    return str(chat_id) in OWNER_CHAT_IDS

# Ensure all handlers are properly registered and async functions are used correctly

# Enhance user experience with better formatting and emojis
async def main_menu(update: Update, context: CallbackContext) -> None:
    menu_keyboard = [
        [InlineKeyboardButton("\U0001F4D6 مشاهده منو", callback_data="menu")],
        [InlineKeyboardButton("\U0001F4DD ثبت کد تغذیه", callback_data="register")],
        [InlineKeyboardButton("\U0001F4C5 مشاهده رزروها", callback_data="show_reservations")],
        [InlineKeyboardButton("\U0001F4DA راهنما", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(menu_keyboard)
    welcome_message = (
        "\U0001F44B خوش آمدید!\n"
        "\U0001F4D1 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:\n"
    )
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_message, reply_markup=reply_markup)

# Update the start command to always show the main menu
async def start(update: Update, context: CallbackContext) -> None:
    await main_menu(update, context)

# Update the `register` function to prompt the user for their feeding code
async def register(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "\U0001F4DD لطفاً کد تغذیه خود را ارسال کنید:"
    )

# Add a new handler to capture the feeding code
async def capture_feeding_code(update: Update, context: CallbackContext) -> None:
    student_id = str(update.effective_user.id)
    code = update.message.text.strip()
    if code.isdigit():  # Ensure the feeding code is numeric
        students[student_id] = code
        await update.message.reply_text(
            f"\U00002705 کد تغذیه شما ({code}) با موفقیت ثبت شد!\n"
            "\U0001F4D1 بازگشت به منوی اصلی:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\U0001F4D1 منوی اصلی", callback_data="menu")]
            ])
        )
    else:
        await update.message.reply_text(
            "\U0001F6AB کد تغذیه باید فقط شامل اعداد باشد. لطفاً دوباره تلاش کنید."
        )

# Ensure Persian day names are displayed in the menu and button functions
persian_days = {
    "saturday": "شنبه",
    "sunday": "یکشنبه",
    "monday": "دوشنبه",
    "tuesday": "سه‌شنبه",
    "wednesday": "چهارشنبه",
    "thursday": "پنج‌شنبه",
    "friday": "جمعه"
}

# Update the `menu` function to handle both message and callback query contexts
async def menu(update: Update, context: CallbackContext) -> None:
    days_keyboard = [
        [InlineKeyboardButton(f"\U0001F4C6 {persian_days[day]}", callback_data=day)] for day in menu_data.keys()
    ]
    reply_markup = InlineKeyboardMarkup(days_keyboard)
    if update.message:
        await update.message.reply_text(
            "\U0001F4D6 لطفاً روز مورد نظر خود را انتخاب کنید:", reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "\U0001F4D6 لطفاً روز مورد نظر خود را انتخاب کنید:", reply_markup=reply_markup
        )

# Update the `register` button logic to prompt for feeding code
# Update the `show_reservations` button logic to handle callback queries
# Fix the `button` function to handle expired or invalid callback queries
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        logger.error(f"Failed to answer callback query: {e}")
        return

    if query.data == "menu":
        await menu(update, context)
    elif query.data == "register":
        await query.message.reply_text(
            "\U0001F4DD لطفاً کد تغذیه خود را ارسال کنید:"
        )
    elif query.data == "show_reservations":
        await show_reservations(update, context)
    elif query.data == "help":
        await help_command(update, context)
    else:
        await query.edit_message_text("گزینه نامعتبر است. بازگشت به منوی اصلی.")
        await main_menu(update, context)

        # Existing logic for day and meal selection
        student_id = str(update.effective_user.id)  # Use effective_user.id consistently as a string
        if student_id not in students:
            await query.edit_message_text(
                "\U0001F6AB لطفاً ابتدا کد تغذیه خود را ثبت کنید با دستور /register."
            )
            return

        if query.data in menu_data:  # If a day is selected
            selected_day = query.data
            context.user_data['selected_day'] = selected_day

            meals = menu_data[selected_day]
            meals_keyboard = [
                [InlineKeyboardButton(f"\U0001F374 صبحانه: {meals['breakfast']}", callback_data=f"{selected_day}_breakfast")],
                [InlineKeyboardButton(f"\U0001F35C ناهار: {meals['lunch']}", callback_data=f"{selected_day}_lunch")],
                [InlineKeyboardButton(f"\U0001F35D شام: {meals['dinner']}", callback_data=f"{selected_day}_dinner")],
                [InlineKeyboardButton("\U0001F4E6 رزرو تمام وعده‌ها", callback_data=f"{selected_day}_all")]
            ]
            reply_markup = InlineKeyboardMarkup(meals_keyboard)
            await query.edit_message_text(
                f"\U0001F4C6 لطفاً وعده مورد نظر خود را برای روز {persian_days[selected_day]} انتخاب کنید:", reply_markup=reply_markup
            )
        else:  # If a meal or all meals are selected
            data = query.data.split("_")
            selected_day = data[0]
            selected_meal = data[1]

            feeding_code = students[student_id]  # Get the feeding code for the user

            if selected_meal == "all":
                meals = menu_data[selected_day]
                if feeding_code not in reservations:
                    reservations[feeding_code] = {}
                reservations[feeding_code][selected_day] = meals
                save_reservations(reservations)

                await query.edit_message_text(
                    f"\U00002705 رزرو شما برای تمام وعده‌های روز {persian_days[selected_day]} ثبت شد:\n"
                    f"\U0001F374 صبحانه: {meals['breakfast']}\n"
                    f"\U0001F35C ناهار: {meals['lunch']}\n"
                    f"\U0001F35D شام: {meals['dinner']}\n"
                    f"\U0001F4DD کد تغذیه شما: {feeding_code}"
                )
            else:
                meal_name = menu_data[selected_day][selected_meal]

                if feeding_code not in reservations:
                    reservations[feeding_code] = {}
                if selected_day not in reservations[feeding_code]:
                    reservations[feeding_code][selected_day] = {}

                reservations[feeding_code][selected_day][selected_meal] = meal_name
                save_reservations(reservations)

                persian_meals = {
                    "breakfast": "صبحانه",
                    "lunch": "ناهار",
                    "dinner": "شام"
                }

                await query.edit_message_text(
                    f"\U00002705 رزرو شما برای وعده {persian_meals[selected_meal]} روز {persian_days[selected_day]} ثبت شد:\n"
                    f"\U0001F374 وعده: {meal_name}\n"
                    f"\U0001F4DD کد تغذیه شما: {feeding_code}"
                )

# Fix the `show_reservations` function to always display Persian day names
async def show_reservations(update: Update, context: CallbackContext) -> None:
    if update.callback_query:
        user = update.callback_query.from_user
    else:
        user = update.effective_user

    chat_id = str(user.id)
    if not is_owner(chat_id):
        error_message = "\U0001F6AB شما اجازه دسترسی به این بخش را ندارید."
        if update.message:
            await update.message.reply_text(error_message)
        elif update.callback_query:
            await update.callback_query.message.reply_text(error_message)
        return

    if not reservations:
        no_reservations_message = "\U0001F4E6 هیچ رزروی ثبت نشده است."
        if update.message:
            await update.message.reply_text(no_reservations_message)
        elif update.callback_query:
            await update.callback_query.message.reply_text(no_reservations_message)
        return

    # Map both Persian and English day names to their corresponding Jalali dates
    jalali_dates = {
        "شنبه": JalaliDate(1404, 2, 1),
        "یکشنبه": JalaliDate(1404, 2, 2),
        "دوشنبه": JalaliDate(1404, 2, 3),
        "سه‌شنبه": JalaliDate(1404, 2, 4),
        "چهارشنبه": JalaliDate(1404, 2, 5),
        "پنج‌شنبه": JalaliDate(1404, 2, 6),
        "جمعه": JalaliDate(1404, 2, 7),
        "saturday": JalaliDate(1404, 2, 1),
        "sunday": JalaliDate(1404, 2, 2),
        "monday": JalaliDate(1404, 2, 3),
        "tuesday": JalaliDate(1404, 2, 4),
        "wednesday": JalaliDate(1404, 2, 5),
        "thursday": JalaliDate(1404, 2, 6),
        "friday": JalaliDate(1404, 2, 7)
    }

    message = "\U0001F4C5 لیست غذاهای رزرو شده:\n"
    for feeding_code, days in reservations.items():
        message += f"\n\U0001F4DD کد تغذیه: {feeding_code}\n"
        for day, meals in days.items():
            persian_day = persian_days.get(day, day)  # Convert to Persian day name
            jalali_date = jalali_dates[day].strftime("%Y/%m/%d")
            message += f"  \U0001F4C6 روز {persian_day} ({jalali_date}):\n"
            for meal, name in meals.items():
                persian_meal = persian_meals.get(meal, meal)
                message += f"    \U0001F374 {persian_meal}: {name}\n"

    if update.message:
        await update.message.reply_text(message)
    elif update.callback_query:
        await update.callback_query.message.reply_text(message)

# Improve the help command with better formatting
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "\U0001F4DA راهنمای استفاده از ربات:\n"
        "\U0001F4CC /start - شروع و نمایش منوی اصلی\n"
        "\U0001F4DD ثبت کد تغذیه - ارسال کد تغذیه به صورت پیام\n"
        "\U0001F4D6 مشاهده منو - انتخاب روز و وعده غذایی\n"
        "\U0001F4C5 مشاهده رزروها - مشاهده لیست غذاهای رزرو شده (فقط برای مالک)\n"
        "\U0001F4DA راهنما - مشاهده این راهنما\n"
        "\U0001F4E6 رزرو تمام وعده‌ها - انتخاب تمام وعده‌های یک روز\n"
    )
    if update.message:
        await update.message.reply_text(help_text)
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text)

import asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Add a function to set bot commands
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "شروع و نمایش منوی اصلی"),
        BotCommand("register", "ثبت کد تغذیه"),
        BotCommand("menu", "مشاهده منوی غذا"),
        BotCommand("show_reservations", "مشاهده لیست غذاهای رزرو شده (فقط برای مالک)"),
        BotCommand("help", "مشاهده راهنما")
    ]
    await application.bot.set_my_commands(commands)

# Add a fallback handler to redirect users to the main menu
async def fallback(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("دستور نامعتبر است. بازگشت به منوی اصلی.")
    await main_menu(update, context)

# Update the main function to include the fallback handler
async def main() -> None:
    application = Application.builder().token("7338644071:AAEex9j0nMualdoywHSGFiBoMAzRpkFypPk").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("show_reservations", show_reservations))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_feeding_code))

    # Set bot commands
    await set_bot_commands(application)

    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())