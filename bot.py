import requests
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Функция получения OAuth2 access_token из refresh_token и client_id
def get_access_token(refresh_token, client_id):
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        'client_id': client_id,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'scope': 'https://graph.microsoft.com/.default offline_access'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()
    return response.json()['access_token']


# Функция получения последнего кода TikTok через Microsoft Graph API
def get_tiktok_code(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    url = "https://graph.microsoft.com/v1.0/me/messages?$search=\"from:no-reply@tiktok.com\"&$top=1"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    messages = response.json().get('value', [])

    if not messages:
        return None

    body_preview = messages[0]['body']['content']
    match = re.search(r'\b(\d{6})\b', body_preview)
    return match.group(1) if match else None

# Обработка сообщений от пользователя
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        mail, mailpass, login, password, refreshtoken, clientid = update.message.text.strip().split('|')
    except ValueError:
        await update.message.reply_text('Неверный формат данных. Используйте mail|mailpass|login|pass|refreshtoken|clientid')
        return

    await update.message.reply_text('Проверяю почту...')

    try:
        access_token = get_access_token(refreshtoken, clientid)
        code = get_tiktok_code(access_token)

        if code:
            await update.message.reply_text(f'Ваш код TikTok: {code}')
        else:
            await update.message.reply_text('Код не найден.')
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {str(e)}')

if __name__ == '__main__':
    bot_token = '7220236534:AAFWqlefe3d0WSoePdbjPstabtzQ0pK3fNU'

    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен...")
    app.run_polling()
