import logging  # Импортируем модуль для логирования
import openai  # Импортируем OpenAI для взаимодействия с ChatGPT
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # Импортируем классы для работы с обновлениями и кнопками Telegram
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters  # Импортируем обработчики и фильтры из библиотеки telegram
from docx import Document  # Импортируем модуль для работы с документами формата .docx
from PyPDF2 import PdfReader  # Импортируем модуль для чтения PDF-файлов
import os  # Импортируем модуль для работы с файловой системой

# OpenAI API ключ
openai.api_key = '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'
TOKEN = '7224157923:AAGDq7QdZpLSgY0SzNPjhBnoaFLdxpfe6UY'

# Включаем логирование с форматированием сообщений и уровнем логирования INFO
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Устанавливаем уровень логирования для httpx на WARNING, чтобы скрыть сообщения уровня INFO
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)  # Создаем логгер для нашего приложения

# Обработчик команды /start, который отправляет приветственное сообщение и кнопку для загрузки файла
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user  # Получаем объект пользователя, который вызвал команду
    # Создаем кнопку для загрузки файла
    keyboard = [
        [InlineKeyboardButton("Upload File", callback_data="upload_file")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)  # Создаем разметку для клавиатуры с кнопкой
    # Отправляем сообщение с кнопкой пользователю
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Please upload a file by clicking the button below and then sending the file.",
        reply_markup=reply_markup
    )

# Обработчик для нажатия кнопки
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query  # Получаем объект CallbackQuery, который содержит информацию о нажатой кнопке
    await query.answer()  # Подтверждаем нажатие кнопки
    # Отправляем сообщение с просьбой загрузить файл
    await query.message.reply_text("Please upload your file now.")

# Функция для чтения содержимого текстового файла
def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:  # Открываем файл для чтения в текстовом режиме с кодировкой utf-8
        return file.read()  # Возвращаем содержимое файла

# Функция для чтения содержимого файла .docx
def read_docx(file_path):
    doc = Document(file_path)  # Открываем документ формата .docx
    return "\n".join([para.text for para in doc.paragraphs])  # Собираем текст всех параграфов документа и возвращаем его

# Функция для чтения содержимого PDF файла
def read_pdf(file_path):
    reader = PdfReader(file_path)  # Создаем объект для чтения PDF файла
    text = ""  # Инициализируем переменную для хранения текста
    for page in reader.pages:  # Проходим по всем страницам PDF файла
        text += page.extract_text()  # Извлекаем текст со страницы и добавляем его к переменной
    return text  # Возвращаем полный текст PDF файла

# Функция для генерации ответа через OpenAI с использованием модели gpt-3.5-turbo
def generate_response(content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Используем модель gpt-3.5-turbo
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": content},
        ],
        max_tokens=1500  # Устанавливаем максимальное количество токенов в ответе
    )
    return response['choices'][0]['message']['content'].strip()  # Возвращаем сгенерированный ответ, очищенный от лишних пробелов


# Обработчик загрузки документов от пользователя
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user  # Получаем объект пользователя
    document = update.message.document  # Получаем объект документа, загруженного пользователем
    file = await document.get_file()  # Получаем файл от пользователя

    # Определяем путь для сохранения загруженного файла
    file_path = f"./{document.file_name}"
    await file.download_to_drive(file_path)  # Сохраняем файл на диск

    # Определяем тип файла и читаем его содержимое
    if document.file_name.endswith('.txt'):
        content = read_txt(file_path)  # Читаем содержимое текстового файла
    elif document.file_name.endswith('.docx'):
        content = read_docx(file_path)  # Читаем содержимое файла .docx
    elif document.file_name.endswith('.pdf'):
        content = read_pdf(file_path)  # Читаем содержимое PDF файла
    else:
        await update.message.reply_text("Unsupported file type.")  # Если формат файла не поддерживается, отправляем сообщение об этом
        os.remove(file_path)  # Удаляем загруженный файл
        return

    # Логируем имя пользователя и полученный файл в консоль
    print(f"User {user.username} sent a file: {document.file_name}")

    # Отправляем содержимое файла в ChatGPT для генерации ответа
    response = generate_response(content)

    # Отправляем сгенерированный ответ обратно пользователю
    await update.message.reply_text(response)

    # Удаляем временный файл после обработки
    os.remove(file_path)

# Функция для обработки команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")

# Функция для отправки сообщений напрямую в ChatGPT
async def chat_with_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user  # Получаем объект пользователя
    message_text = update.message.text  # Получаем текст сообщения от пользователя

    # Логируем имя пользователя и отправленное сообщение в консоль
    print(f"User {user.username} sent a message: {message_text}")

    # Отправляем сообщение пользователя в ChatGPT для генерации ответа
    response = generate_response(message_text)

    # Отправляем сгенерированный ответ обратно пользователю
    await update.message.reply_text(response)

def main() -> None:
    """Start the bot."""
    # Создаем объект приложения и передаем токен вашего бота
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))  # Обработчик команды /start
    application.add_handler(CommandHandler("help", help_command))  # Обработчик команды /help

    # Регистрируем обработчик нажатий на кнопки
    application.add_handler(CallbackQueryHandler(button_callback))  # Обработчик нажатий на кнопки

    # Регистрируем обработчик загрузки документов
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))  # Обработчик для всех типов документов

    # Регистрируем обработчик сообщений для общения с ChatGPT
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_gpt))  # Обработчик для текстовых сообщений

    # Запуск бота в режиме polling (постоянное получение обновлений)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()  # Запускаем основную функцию для старта бота
