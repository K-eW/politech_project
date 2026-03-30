from config import *
from telebot.async_telebot import *
from SQL.user_base import *
from get_report import *
from pathlib import Path
from grafics import *

bot = AsyncTeleBot(TOKEN)

BASE_DIR = Path(__file__).resolve().parent.parent



@bot.message_handler(commands=['start'])
async def start(message):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text="📊 Получить отчет", callback_data="report"))
    markup.add(types.InlineKeyboardButton(text="📈 Получить графики", callback_data='graphs'))

    await bot.reply_to(
        message=message,
        text="👋 Привет! Я – бот для аналитики ваших продаж",
        reply_markup=markup
    )

    commands = [
        types.BotCommand(command='start', description='🔄 Перезапуск')
    ]

    await bot.set_my_commands(commands, scope=types.BotCommandScopeChat(message.chat.id))

    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)





@bot.message_handler(content_types=['document'])
async def save_user_document(message):
    user = get_user_state(message.chat.id)
    mode = user.get_mode().split('__')[0]
    type_file = user.get_mode().split('__')[1]

    if mode == '/report':
        file_name = message.document.file_name
        file_info = await bot.get_file(message.document.file_id)



        if '.csv' not in file_name:
            await bot.send_message(
                chat_id=message.chat.id,
                text="❌ Пожалуйста, отправьте файл в формате \".csv\""
            )

            return
        if type_file not in ['menu_plan', 'sales_fact']:
            await bot.reply_to(
                message,
                f"❌ Ожидаются: \"menu_plan.csv\" или \"sales_fact.csv\"\n"
                f"Вы прислали: `{file_name}`"
            )
            return

        downloaded_file = await bot.download_file(file_info.file_path)

        if type_file == 'menu_plan':
            message_doc = await bot.send_message(
                chat_id=message.chat.id,
                text="Получен новый файл план продаж"
            )
            file_name = 'menu_plan.csv'

        elif type_file == 'sales_fact':
            message_doc = await bot.send_message(
                chat_id=message.chat.id,
                text="Получен новый файл фактических продаж"
            )
            file_name = 'sales_fact.csv'


        user_dir = f"user_data/{message.chat.id}"
        os.makedirs(user_dir, exist_ok=True)

        file_path = os.path.join(user_dir, file_name)

        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)


        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )

        await asyncio.sleep(4)

        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=message_doc.message_id
        )


        if os.path.exists(f'{user_dir}/menu_plan.csv') and os.path.exists(f'{user_dir}/sales_fact.csv'):
            message_bot = await bot.send_message(
                chat_id=message.chat.id,
                text="Все файлы получены\n"
                     "Начинаю обработку..."
            )
            styled, sum_table = await get_report(message.chat.id)

            await bot.delete_message(chat_id=message.chat.id, message_id=message_bot.message_id)

            os.remove(f'{user_dir}/menu_plan.csv')
            os.remove(f'{user_dir}/sales_fact.csv')

            with pd.ExcelWriter(f'{user_dir}/report.xlsx', engine='openpyxl') as writer:
                styled.to_excel(writer, sheet_name='Отчет', index=False)

                worksheet = writer.sheets['Отчет']

                for column in sum_table.columns:
                    column_length = max(
                        sum_table[column].astype(str).map(len).max(),
                        len(column)) + 2
                    col_idx = sum_table.columns.get_loc(column) + 1
                    worksheet.column_dimensions[chr(65 + col_idx - 1)].width = column_length

            sum_table.to_csv(f"{user_dir}/report.csv", index=False)

            with open(f"{user_dir}/report.xlsx", "rb") as f:
                await bot.send_document(document=f, chat_id=message.chat.id)

            markup = types.InlineKeyboardMarkup()

            markup.add(types.InlineKeyboardButton(text="📊 Получить отчет", callback_data="report"))
            markup.add(types.InlineKeyboardButton(text="📈 Получить графики", callback_data='graphs'))

            await bot.send_message(
                chat_id=message.chat.id,
                text=("✅ Готово!\n"
                     "Выберите следующее действие:"),
                reply_markup=markup
            )

    elif mode == '/graphs':
        if not os.path.exists(f'user_data/{message.chat.id}/report.xlsx'):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text="📊 Получить отчет", callback_data="report"))

            await bot.send_message(
                chat_id=message.chat.id,
                text="⚠️ Сначала получите отчет через `📊 Получить отчет`",
                reply_markup=markup
            )
            return

        await get_graphs(message.chat.id)

        await bot.send_media_group(
            chat_id=message.chat.id,
            media=[telebot.types.InputMediaPhoto(open(f'user_data/{message.chat.id}/plan_vs_fact.png', 'rb')),
                    telebot.types.InputMediaPhoto(open(f'user_data/{message.chat.id}/revenue_by_day.png', 'rb')),
                    telebot.types.InputMediaPhoto(open(f'user_data/{message.chat.id}/status_pie.png', 'rb'))]
        )



@bot.callback_query_handler(func=lambda call: call.data in ['menu_plan', 'sales_fact'])
async def get_doc(call):
    types_doc = {
        'menu_plan': 'План продаж',
        'sales_fact': 'Реальные продажи'
    }

    await bot.answer_callback_query(call.id, f'Отправьте {types_doc[call.data]}')
    user = get_user_state(call.message.chat.id)
    mode = user.get_mode().split('__')[0]
    user.set_mode(f'{mode}__{call.data}')

    await save_user_to_data(call.message.chat.id)


    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('📋 План продаж' if call.data == "sales_fact"
                                          else '🛒 Реальные продажи',

                                          callback_data='menu_plan' if call.data == "sales_fact"
                                          else 'sales_fact'))

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"Ожидаю файл \"{types_doc[call.data]}\"",
        reply_markup=markup
    )




@bot.callback_query_handler(func=lambda call: call.data == 'report')
async def report(call):
    await bot.answer_callback_query(call.id)

    message = call.message
    user = get_user_state(message.chat.id)
    user.set_mode('/report')
    await save_user_to_data(message.chat.id)

    await bot.delete_message(message.chat.id, message.id)

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('📋 План продаж', callback_data='menu_plan'))
    markup.add(types.InlineKeyboardButton('🛒 Реальные продажи', callback_data='sales_fact'))

    await bot.send_message(
        chat_id=message.chat.id,
        text=("Необходимы 2 файла в формате `.csv`\n"
              "Файл с планом продаж (menu_plan.csv)\n"
              "Файл с фактической статистикой (sales_fact.csv)\n"
              "Пример:"),
        parse_mode='markdown'
    )

    await bot.send_media_group(
        chat_id=message.chat.id,
        media=[telebot.types.InputMediaDocument(open(f'{BASE_DIR}/sales_fact.csv', "rb")),
               telebot.types.InputMediaDocument(open(f'{BASE_DIR}/menu_plan.csv', "rb"))]
    )

    await asyncio.sleep(2)

    await bot.send_message(
        chat_id=message.chat.id,
        text="Теперь выберите какой документ вы хотите загрузить:",
        reply_markup=markup
    )

@bot.callback_query_handler(func = lambda call: call.data == 'graphs')
async def graphs(call):
    await bot.answer_callback_query(call.id)

    message = call.message
    user = get_user_state(message.chat.id)
    user.set_mode('/graphs__none')
    await save_user_to_data(message.chat.id)


    await save_user_document(message)



async def main():
    try:
        await init_user_base()
        logging.info("✅ Все данные загружены. Бот запускается...")
        await asyncio.sleep(1)
        await bot.infinity_polling()
    finally:
        await close_db()
        logging.info("❌ База данных закрыта")

if __name__ == '__main__':
    asyncio.run(main())

