import sqlite3
from flask import Flask, request, render_template
import os
from datetime import datetime
from scripts.config import user_password, user_login, user_db
from mysql.connector import connect, Error


application = Flask(__name__)
output_dir = 'generated_charts'

def convert_date_format(date_str):
    # Преобразование строки в объект datetime
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    # Форматирование объекта datetime обратно в строку в новом формате
    new_date_str = date_obj.strftime('%d.%m.%Y')  # Изменение на точку в качестве разделителя
    return new_date_str

def get_num_vacancies_and_date(profession):
    try:
        conn = connect(
            host="localhost",
            user=user_login,
            password=user_password,
            database=user_db
        )
    except Error as e:
        print(e)
        
    try:
        cursor = conn.cursor()
        # Ваш SQL-запрос корректен и хорошо использовать параметризованный запрос
        cursor.execute("SELECT count, date FROM vacancies WHERE profession= %s ORDER BY date DESC LIMIT 1", (profession,))
        row = cursor.fetchone()
        if row:
            num_vacancies, last_date = row
        else:
            num_vacancies, last_date = None, None
    finally:
        cursor.close()
        conn.close()
    return num_vacancies, last_date

professions_dict = {
    "Data analyst": 'name:(!"data analyst" or !"аналитик данных" )'
    "Product analyst": 'name:("Product analyst" or "Продуктовый аналитик")',
    "Data scientist": 'name:("data scientist" or "data science" or "datascience")',
    "ML engineer": 'name:("ml engineer" or "Machine learning" or "Машинное обучение" or "ml" or "машинного обучения" or "nlp" or "computer vision")',
    "Data engineer": 'name:(!"data engineer" or !"инженер данных" or "специалист по данным" or "Специалист по работе с данными" or "дата инженер")',
    "Python developer": 'name:(python or django or drf or backend or fastapi or flask)  and description:(python or django or drf or fastapi or flask)',
    "Golang developer": 'name:(!"go" or !"golang")',
    "Java developer": 'name:(!"java")',
    "Frontend developer": '("frontend" or "front end" or "react" or "vue.js") and name:("frontend" or "front-end")'
    "Android developer": 'name:("Android" or "Андроид") and description:("kotlin" or "java" or "sdk" or !"мобильных приложений")',
    "IOS developer": 'name:("ios" or "swift")',
    "QA engineer": 'name:("QA engineer" or "тестировщик" or "по тестированию" or "QA инженер")',
    "System analyst": 'name:("system data analyst" or "system analyst" or "системный аналитик")'
    "Business analyst": 'name:("Business Аnalyst" or "business analyst" or "бизнес аналитик" or "bi-аналитик")',
    "UX UI designer": 'name:(!"UX/UI дизайнер" or !"UX/UI designer" or !"UI/UX designer" or "!UI/UX дизайнер" or !"дизайнер интерфейсов")',
    "C C++ developer": 'description:(!"C++") and name:(!"программист" or !"developer" or !"разработчик" or !"C++")',
    "1C developer": '"1C developer" or "1C разработчик" or "1C программист" or "программист 1C" or "разработчик 1C"',
    "PHP developer": 'name:("PHP")',
    "Product manager": 'name:("Product manager" or "продукт менеджер" or "продуктовый менеджер")',
    "Project manager": 'name:(!"Project manager" or !"проджект менеджер" or !"менеджер проекта" or !"менеджер проектов" or !"проектный менеджер" or !"руководитель проектов" or !"руководитель проекта")'
}

professions = list(professions_dict)

charts_info = [{'title': 'Ключевые навыки', 'description': 'Навыки, которые чаще всего указываются работодателями в вакансиях (чем больше навыков совпадает из вакансии с навыками в вашем резюме, тем больше шансов пройти скрининг'}, 
               {'title': 'Ключевые слова', 'description': 'Список самых частых технологий из описаний вакансий'}, 
               {'title': 'Зарплата/опыт', 'description': 'Зависимость зарплаты от опыта работы'}, 
               {'title': 'Зарплаты', 'description': 'Распределение зарплат'},
               {'title': 'Опыт работы', 'description': 'Круговая диаграмма, отображающая частотность требуемого опыта'}, 
               {'title': 'Распространение по России', 'description': 'Показывает какой процент из всех вакансий этой профессии находится в каждом из регионов'}, 
               {'title': 'Динамика количества вакансий', 'description': 'Ежедневное изменение количества вакансий по этой профессии'}]

@application.route('/', methods=['GET', 'POST'])
def index():
    selected_profession = professions[0]

    #charts_html = ""
    charts_html = []

    if request.method == 'POST':
        selected_profession = request.form['profession']
        
    num_vacancies, last_date = get_num_vacancies_and_date(selected_profession)
    
    for i in range(7):  # Допустим, у вас 7 графиков
        filename = f'{selected_profession}_chart_{i}.html'
        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                charts_html.append(f.read())
        except FileNotFoundError:
            charts_html.append(f'<p>График {filename} не найден</p>')
    
    if len(charts_html) != len(charts_info):
        raise ValueError("Количество элементов в 'charts' и 'charts_info' должно быть одинаковым")
    
    search_url = f"https://hh.ru/search/vacancy?text={professions_dict[selected_profession]}"
    
    return render_template('index.html', professions=professions, selected_profession=selected_profession, 
                           charts=charts_html, charts_info=charts_info, num_vacancies=num_vacancies, 
                           search_url=search_url, last_date=convert_date_format(last_date))

if __name__ == '__main__':
    application.run(debug=True)
