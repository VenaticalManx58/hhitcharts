import requests
import json
import os
import mysql.connector
os.environ["OMP_NUM_THREADS"] = "1"
import pandas as pd
from collections import Counter
import re
import bleach
import nltk
from nltk.corpus import stopwords
import plotly.graph_objs as go
import plotly.io as pio
import plotly.express as px
import os
import datetime
from datetime import date
from config import HEADERS, user_login, user_password, user_db
import sys
import numpy as np
import seaborn as sns

nltk.download('stopwords')
pd.options.mode.chained_assignment = None  # default='warn'

professions_dict_1 = {
    "Product analyst": '"Product analyst" or "Продуктовый аналитик"',
    "Data scientist": '"data scientist"  or "data science"',
    "ML engineer": '"ml engineer" or "Machine learning" or "Машинное обучение" or "ml"',
    "Data engineer": '"data engineer" or "Инженер данных"',
    "Python developer": '"python" or "django" or "drf" or "flask" or "fastapi"',
    "Golang developer": '"golang" or "go"',
    "Java developer": '"java"',
    "Frontend developer": '"frontend" or "front end" or "react" or "vue.js"'
}
# 8
professions_dict_2 = {
    "Android developer": 'name:("Android" or "Андроид") and description:("kotlin" or "java" or "sdk")',
    "IOS developer": 'name:("ios" or "swift")',
    "QA engineer": '"QA engineer" or "тестировщик" or "по тестированию"',
    "System analyst": '"system analyst" or "системный аналитик"'
}
# 12
professions_dict_3 = {
    "Business analyst": '"business analyst" or "бизнес аналитик" or "bi-аналитик"',
    "UX UI designer": '"UX/UI" "UI/UX"',
    "C C++ developer": '"C++"',
    "1C developer": '"1C developer" or "1C разработчик" or "1C программист" or "программист 1C" or "разработчик 1C"',
    "PHP developer": '"PHP"',
    "Product manager": '!"Product manager" or !"продукт менеджер" or !"продуктовый менеджер"',
    "Project manager": '!"Project manager" or !"проджект менеджер" or !"менеджер проекта" or !"менеджер проектов" or !"проектный менеджер" or !"руководитель проектов" or !"руководитель проекта"'
}
# 19

output_dir = 'generated_charts'

os.makedirs(output_dir, exist_ok=True)

def get_exchange_rate():
    # URL для получения XML данных с курсами валют
    url = 'https://www.cbr.ru/scripts/XML_daily.asp'
    
    # Запрос к API
    response = requests.get(url)
    
    # Проверка успешности запроса
    if response.status_code != 200:
        print("Ошибка при запросе данных")
        return None
    
    # Парсинг XML данных
    from xml.etree import ElementTree as ET
    tree = ET.fromstring(response.content)

    # Переменные для хранения курсов
    usd_to_rub = None
    eur_to_rub = None
    
    # Поиск курсов в XML данных
    for valute in tree.findall('Valute'):
        char_code = valute.find('CharCode').text
        value = valute.find('Value').text
        nominal = valute.find('Nominal').text
        
        if char_code == 'USD':
            usd_to_rub = float(value.replace(',', '.')) / float(nominal.replace(',', '.'))
        elif char_code == 'EUR':
            eur_to_rub = float(value.replace(',', '.')) / float(nominal.replace(',', '.'))
    
    return usd_to_rub, eur_to_rub

usd, eur = get_exchange_rate()

def get_vacancies_ids(url: str):
    response = requests.get(url)
    df = json.loads(response.text)
    pages = df['pages']
    per_page = df['per_page']
    df = pd.json_normalize(df['items'])
    result_array=[]
    for page in range(pages):
        page_response = requests.get(url, headers=HEADERS, params={'page': page})
        page_data = json.loads(page_response.text)
        page_data = page_data['items']
        for vacancy in page_data:
            result_array.append(vacancy['id'])
    return result_array

def get_vacancy_key_skills(data_key_skills):
    if data_key_skills == []: return []
    return [skill['name'] for skill in data_key_skills]

stop_words = set(stopwords.words('english'))
my_stop_words = ['b', 'it', 'hr', '1', "2", "3", "4", "5", "6", "7", "8", "9", "etc",
                'it', '00', '10', '100', 'quot', '11', '12', '13', '14', '15', '16', '17', '18',
                'and', 'the', 'to', 'end', '39', 'ru', 'of', '000', 'you', 'in', 'skills', 'back', 'with', 'for',
                'we', 'on',
                '19', 'e', 'er', '30', '20', '0', 'a', 'o', '50',
                'be', 'our', 'will', 'is', 'your', 'as', 'that',
                'including', 'an', 'new', 'are', 'at', 'by',
                'other', 'have', 'all', 'about', 'us', 'ozon', 'music',
                's7', 'on', '1000', 'or', 'off', '70', '200',
                'based', 'ready', '60', '80', '90', '400', 'what',
                'from', '40', 'war', '24', 'skyeng', 'tinkoff', '09',
                '2015', 'wildberries', '08', '300', '25', '45', 'need',
                'do', '28', '500', '2017', '09', '112', '103',
                '122', '2008', '232', '485', '3000', 'll', '2022',
                '400', 'project', 'manager', 'intermediate', 'ux', 'ui', 'ux/ui', 'ui/ux', 'data', 'science', 'learning', 'scientist']


def clean_description(text):
    return [word for word in text if word not in stop_words and word not in my_stop_words]

def get_vacancy_keywords(data_description):
    txt = bleach.clean(data_description, tags=[], strip=True)
    txt = re.findall(r'\b[a-zA-Z]+(?:[-/][a-zA-Z]+)*\b', txt)
    txt = [word.lower() for word in txt]
    words_list = clean_description(txt)
    return words_list

def safe_average(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return (a+b)/2


def professional_role_skills_analyze(vacancies_ids): #потом заменить на url
    skills = []
    keywords = []
    salary_exp = []
    for vacancy_id in vacancies_ids:
        response = requests.get(f'https://api.hh.ru/vacancies/{vacancy_id}', headers=HEADERS)
        data = json.loads(response.text)
        try:
            sal = data['salary']
            if sal != None:
                if (sal['currency'] == 'RUR'):
                    cf = 1
                elif (sal['currency'] == 'USD'):
                    cf = usd
                elif (sal['currency'] == 'EUR'):
                    cf = eur
                else:
                    cf = 0
                if cf != 0:
                    salary_exp.append((data['experience']['name'], round(cf*safe_average(sal['from'], sal['to']))))       
        except:
            print(data)
            break
        try:      
            skills += get_vacancy_key_skills(data['key_skills'])
            keywords += get_vacancy_keywords(data['description'])
        except:
            print(data)
            break
    return Counter(skills).most_common(15), Counter(keywords).most_common(15), salary_exp

def generate_charts(profession, c):
    charts = []
    url = f'https://api.hh.ru/vacancies?text={profession[1]}&clusters=true'

    vacancies_ids = get_vacancies_ids(url)
    # keyskills and keywords and salary exp data extract
    skills_array, keywords_array, salary_exp = professional_role_skills_analyze(vacancies_ids)

    #keyskills graph
    x_data = [item[0] for item in skills_array]
    y_data = [item[1] for item in skills_array]
    fig = go.Figure([go.Bar(x=y_data, y=x_data, orientation='h', width=0.9, text=x_data, textposition='auto')])
    fig.update_layout(yaxis=dict(categoryorder='total ascending', autorange=True), margin=dict(l=20, r=20, t=20, b=20))
    fig.update_yaxes(showticklabels=False)
    chart_html = pio.to_html(fig, full_html=False)
    charts.append(chart_html)

    #keywords graph
    x_data = [item[0] for item in keywords_array]
    y_data = [item[1] for item in keywords_array]
    fig = go.Figure([go.Bar(x=y_data, y=x_data,  orientation='h', width=0.9, text=x_data, textposition='auto')])
    fig.update_layout(yaxis=dict(categoryorder='total ascending', autorange=True), margin=dict(l=20, r=20, t=20, b=20))
    fig.update_yaxes(showticklabels=False)
    chart_html = pio.to_html(fig, full_html=False)
    charts.append(chart_html)

    # salary / experience
    x_data = [item[0] for item in salary_exp]
    y_data = [item[1] for item in salary_exp]
    
    temp_df = pd.DataFrame({'x': x_data, 'y': y_data})
    temp_df = temp_df[temp_df.y < temp_df.y.quantile(.9)]
    
    fig = go.Figure()
    experiences = ['Нет опыта', 'От 1 года до 3 лет', 'От 3 до 6 лет', 'Более 6 лет']

    for exper in experiences:
        fig.add_trace(go.Violin(x=temp_df['x'][temp_df['x'] == exper],
                                y=temp_df['y'][temp_df['x'] == exper],
                                name=exper,
                                box_visible=True,
                                meanline_visible=True))

    chart_html = pio.to_html(fig, full_html=False)
    charts.append(chart_html)
    

    response = requests.get(url, headers=HEADERS)
    pd.options.mode.chained_assignment = None # default='warn'
    data_request = json.loads(response.text)
    clusters_df = pd.json_normalize(data_request['clusters'])
    clusters_df = clusters_df.explode('items').reset_index(drop=True)
    new_df = clusters_df.join(pd.DataFrame(clusters_df.pop('items').values.tolist()).reset_index(drop=True), lsuffix='_original', rsuffix='_items')
    new_df.drop(columns=['url'], inplace=True)
    new_df = new_df[(new_df['name_items'] != 'Россия') & (new_df['name_items'] != 'Указан')]
    new_df['sum_by_id'] = new_df.groupby('id')['count'].transform('sum')
    new_df.fillna({'sum_by_id':0}, inplace=True)
    new_df['count_percentage'] = new_df['count']/new_df['sum_by_id']*100
    new_df.fillna({'count_percentage':0}, inplace=True)

    # salary
    step_size = 31000
    min_salary = int(np.floor(min(y_data) / step_size) * step_size)
    max_salary = int(np.ceil(max(y_data) / step_size) * step_size)
    bins = np.arange(min_salary, max_salary + step_size, step_size)

    hist_data = np.histogram(y_data, bins=bins)
    bin_edges = hist_data[1]
    bin_counts = hist_data[0] / sum(hist_data[0]) * 100  # Преобразование в проценты

    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    fig = go.Figure()
    fig.add_trace(go.Bar(x=bin_centers, y=bin_counts, width=bin_edges[1] - bin_edges[0], name='Гистограмма'))

    mean_salary = round(np.mean(y_data))
    median_salary = round(np.median(y_data))

    fig.add_vline(x=mean_salary, line=dict(color="Orange", width=2, dash="dashdot"), annotation_text=f"Среднее: {mean_salary}", annotation_position="top right")
    fig.add_vline(x=median_salary, line=dict(color="Green", width=2, dash="dashdot"), annotation_text=f"Медиана: {median_salary}", annotation_position="top left")

    sns_kde = sns.kdeplot(y_data, bw_adjust=0.4)  # Увеличьте bw_adjust для более гладкой линии
    kde_x = sns_kde.get_lines()[0].get_data()[0]
    kde_y = sns_kde.get_lines()[0].get_data()[1]

    kde_y_scaled = kde_y / kde_y.max() * max(bin_counts)

    fig.add_trace(go.Scatter(x=kde_x, y=kde_y_scaled, mode='lines', name='KDE', line=dict(color='red')))

    fig.update_layout(
        xaxis_title='Зарплата',
        yaxis_title='Процент',
        showlegend=False,
        margin=dict(t=0, l=0, r=0, b=0)
    )

    chart_html = pio.to_html(fig, full_html=False)
    charts.append(chart_html)

    # experience
    experience_df = new_df.loc[new_df['id'] == 'experience']
    fig = px.pie(experience_df, names='name_items', values='count_percentage', labels={'name_items': 'Опыт', 'count_percentage': 'Проценты'})
    fig.update_layout(legend=dict(
    yanchor="top",
    y=0.99,
    xanchor="right",
    x=0.3),
    margin=dict(t=0, l=0, r=0, b=0))
    fig.update_layout(
        autosize=True
    )
    chart_html = pio.to_html(fig, full_html=False)
    charts.append(chart_html)

    # geographical
    area_df = new_df.loc[new_df['id'] == 'area']

    area_df.drop(['name_original'], axis=1, inplace=True)
    area_df.reset_index(drop=True, inplace=True)
    area_df.reset_index(inplace=True)

    countries = requests.get('https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/russia.geojson').text
    countries = json.loads(countries)
    regions_republic_1 = ['Бурятия', 'Тыва', 'Адыгея', 'Татарстан', 'Марий Эл',
                        'Чувашия', 'Северная Осетия - Алания', 'Алтай',
                        'Дагестан', 'Ингушетия', 'Башкортостан']
    regions_republic_2 = ['Удмуртская республика', 'Кабардино-Балкарская республика',
                        'Карачаево-Черкесская республика', 'Чеченская республика']
    for k in range(len(countries['features'])):
        countries['features'][k]['id'] = k
        if countries['features'][k]['properties']['name'] in regions_republic_1:
            countries['features'][k]['properties']['name'] = 'Республика ' + countries['features'][k]['properties']['name']
        elif countries['features'][k]['properties']['name'] == 'Ханты-Мансийский автономный округ - Югра':
            countries['features'][k]['properties']['name'] = 'Ханты-Мансийский АО'
        elif countries['features'][k]['properties']['name'] in regions_republic_2:
            countries['features'][k]['properties']['name'] = countries['features'][k]['properties']['name'].title()
    
    region_id_list = []
    regions_list = []
    for k in range(len(countries['features'])):
        region_id_list.append(countries['features'][k]['id'])
        regions_list.append(countries['features'][k]['properties']['name'])
    df_regions = pd.DataFrame()
    df_regions['region_id'] = region_id_list
    df_regions['region_name'] = regions_list

    area_df = area_df.merge(df_regions, left_on='name_items', right_on='region_name')

    fig = go.Figure(go.Choroplethmapbox(geojson=countries,
                           locations=area_df['region_id'],
                           z=area_df['count_percentage'],

                           text=area_df['name_items'],
                           colorscale=[[0, 'rgb(145,240,134)'],
                                       [0.05, 'rgb(17,130,59)'],
                                       [0.1, 'rgb(0,77,37)'],
                                       [1, 'rgb(2,35,28)']],

                           colorbar_thickness=20,
                           hovertemplate='<b>%{text}</b>'+ '<br>' +
                                         'Процент вакансий: %{z}' +
                                         '<extra></extra>',
                           hoverinfo='text, z',
                           colorbar_title="Проценты"))

    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=1, mapbox_center = {"lat": 66, "lon": 94})
    fig.update_traces(marker_line_width=1)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    chart_html = pio.to_html(fig, full_html=False)
    charts.append(chart_html)

    # update new daily data for number of vacancies
    today = date.today().isoformat()
    count = data_request['found']
    c.execute('INSERT INTO vacancies (profession, date, count) VALUES (%s, %s, %s)',
              (profession[0], today, count))
    
    # change in the number of vacancies
    c.execute('SELECT date, count FROM vacancies WHERE profession= %s ORDER BY date', (profession[0],))
    rows = c.fetchall()
    dates = [datetime.datetime.strptime(row[0], '%Y-%m-%d') for row in rows]
    counts = [row[1] for row in rows]
    fig = px.line(x=dates, y=counts, labels={'x': 'Даты', 'y':'Количество вакансий'})
    chart_html = pio.to_html(fig, full_html=False)
    charts.append(chart_html)


    return charts


if __name__ == '__main__':
    argument = sys.argv[1]
    if argument == '1':
        professions = professions_dict_1
    elif argument == '2':
        professions = professions_dict_2
    elif argument == '3':
        professions = professions_dict_3
    else:
        raise Exception("no console argument")
    count = 0
    conn = mysql.connector.connect(
        host="localhost",
        user=user_login,
        password=user_password,
        database=user_db
        )
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vacancies
             (profession TEXT, date TEXT, count INTEGER)''')
    for profession in professions.items():
        charts = generate_charts(profession, c)
        for i, chart in enumerate(charts):
            filename = f'{profession[0]}_chart_{i}.html'
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chart)
    conn.commit()
    conn.close()
