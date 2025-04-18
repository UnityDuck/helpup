from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, filename='app.log',
                   format='%(asctime)s %(levelname)s %(name)s %(message)s')

# Словарь с картинками 3 городов
cities = {
    'москва': ['1540737/daa6e420d33102bf6947'],
    'нью-йорк': ['1652229/728d5c86707054d4745f'],
    'париж': ["1652229/f77136c2364eb90a3ea8"]
}

# Словарь для хранения данных пользователей
sessionStorage = {}

@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)

def handle_dialog(res, req):
    user_id = req['session']['user_id']
    
    if req['session']['new']:
        # Новая сессия - начинаем новую игру
        sessionStorage[user_id] = {
            'game_started': True,
            'city_to_guess': None,
            'attempts': 0
        }
        start_new_game(res, user_id)
        return
    
    # Проверяем, не запрошена ли помощь
    if 'помощь' in req['request']['original_utterance'].lower():
        show_help(res, user_id)
        return
    
    # Если игра уже идет
    if sessionStorage[user_id]['game_started']:
        process_guess(res, req, user_id)

def show_help(res, user_id):
    """Показывает справку о игре, сохраняя текущее состояние"""
    help_text = (
        "Это игра 'Угадай город'. Я показываю изображение одного из трех городов: "
        "Москва, Нью-Йорк или Париж. Твоя задача - угадать, какой это город. "
        "Можешь сказать 'Сдаюсь', если не знаешь ответ. "
        "Игра продолжается - попробуй угадать город!"
    )
    
    res['response']['text'] = help_text
    # Добавляем кнопку помощи в интерфейс
    res['response']['buttons'] = [
        {
            'title': 'Помощь',
            'hide': True
        }
    ]
    
    # Если игра уже начата, показываем снова картинку города
    if sessionStorage[user_id]['city_to_guess']:
        res['response']['card'] = {
            'type': 'BigImage',
            'image_id': cities[sessionStorage[user_id]['city_to_guess']][0],
            'title': 'Угадай город!',
            'description': 'Какой это город?'
        }

def start_new_game(res, user_id):
    # Выбираем случайный город из 3 возможных
    city = random.choice(list(cities.keys()))
    sessionStorage[user_id]['city_to_guess'] = city
    sessionStorage[user_id]['attempts'] = 0
    
    # Показываем картинку города
    res['response']['card'] = {
        'type': 'BigImage',
        'image_id': cities[city][0],
        'title': 'Угадай город!',
        'description': 'Какой это город?'
    }
    res['response']['text'] = 'Я загадала один из трех городов: Москва, Нью-Йорк или Париж. Попробуй угадать!'
    # Добавляем кнопку помощи
    res['response']['buttons'] = [
        {
            'title': 'Помощь',
            'hide': True
        }
    ]

def process_guess(res, req, user_id):
    user_input = req['request']['original_utterance'].lower()
    city_to_guess = sessionStorage[user_id]['city_to_guess']
    
    # Обработка команды "сдаюсь"
    if any(word in user_input for word in ['сдаюсь', 'не знаю']):
        res['response']['text'] = f'Это был {city_to_guess.title()}. Давай попробуем другой город!'
        # Сразу начинаем новую игру
        start_new_game(res, user_id)
        return
    
    # Проверяем ответ пользователя
    sessionStorage[user_id]['attempts'] += 1
    
    if user_input == city_to_guess.lower():
        # Пользователь угадал
        res['response']['text'] = f'Правильно! Это {city_to_guess.title()}. ' \
                                f'Ты угадал с {sessionStorage[user_id]["attempts"]} попытки. ' \
                                'Сейчас я загадаю новый город!'
        # Сразу начинаем новую игру
        start_new_game(res, user_id)
    else:
        # Пользователь не угадал
        res['response']['text'] = 'Неправильно. Попробуй еще раз!'
        res['response']['card'] = {
            'type': 'BigImage',
            'image_id': cities[city_to_guess][0],
            'title': 'Попробуй еще раз!',
            'description': 'Какой это город? Москва, Нью-Йорк или Париж?'
        }
        # Добавляем кнопку помощи
        res['response']['buttons'] = [
            {
                'title': 'Помощь',
                'hide': True
            }
        ]

if __name__ == '__main__':
    app.run()
    