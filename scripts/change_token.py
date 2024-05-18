import requests
import re
from config import HEADERS, CLIENT_ID, CLIENT_SECRET

# Функция для получения нового токена
def get_new_token():
    url = 'https://hh.ru/oauth/token'  # Замените на ваш URL
    token_params = {
        'grant_type': 'client_credentials',
        'client_id': f'{CLIENT_ID}',
        'client_secret': f'{CLIENT_SECRET}'
    }

    response = requests.post(url, params=token_params)
    
    if response.status_code == 200:
        print(response.json().get('access_token'))
        return response.json().get('access_token')
    else:
        raise Exception(f"Failed to get new token: {response.status_code}, {response.text}")

# Функция для обновления токена в файле config.py
def update_config_file(new_token):
    config_file_path = 'config.py'
    
    # Чтение содержимого файла
    with open(config_file_path, 'r') as file:
        content = file.read()
    
    # Обновление токена с использованием регулярного выражения
    updated_content = re.sub(r"ACCESS_TOKEN\s*=\s*'.*'", f"ACCESS_TOKEN = '{new_token}'", content, count=1)
    
    # Запись обновленного содержимого обратно в файл
    with open(config_file_path, 'w') as file:
        file.write(updated_content)

if __name__ == "__main__":
    try:
        new_token = get_new_token()
        update_config_file(new_token)
        print("Token successfully updated.")
    except Exception as e:
        print(f"An error occurred: {e}")
