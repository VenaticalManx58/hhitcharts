#вам нужно вставить ваши данные
CLIENT_ID = '_'
CLIENT_SECRET = '_'
ACCESS_TOKEN = '_'
# одинарные кавычки это важно! для автообновления
EMAIL = '_'
APP_NAME = '_'

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'User-Agent': f'{APP_NAME} ({EMAIL})',
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

# данные для подключения к mysql db
user_login = '_'
user_password = '_'
user_db = '_'