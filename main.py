from telebot import types
import telebot
import json
import os

TOKEN = '8154113615:AAE5pLcIHwbzFpBqqyK3Qna9JNauOmvyCkQ'

bot = telebot.TeleBot(TOKEN)


menu_items = [
        {"name": "Грибной суп", "price": "450 руб.", "photo": "mushroom_soup.png"},
        {"name": "Салат Цезарь", "price": "550 руб.", "photo": "caesar.png"},
        {"name": "Утка с апельсинами", "price": "700 руб.", "photo": "duck_orange.png"},
        {"name": "Бефстроганов", "price": "650 руб.", "photo": "stroganoff.png"},
        {"name": "Ризотто", "price": "500 руб.", "photo": "risotto.png"},
        {"name": "Тирамису", "price": "400 руб.", "photo": "tiramisu.png"},
        {"name": "Блины", "price": "300 руб.", "photo": "pancakes.png"},
        {"name": "Паста Карбонара", "price": "550 руб.", "photo": "carbonara.png"},
        {"name": "Гаспачо", "price": "350 руб.", "photo": "gazpacho.png"},
        {"name": "Фалафель", "price": "400 руб.", "photo": "falafel.png"}
]


def get_cart(client_id):
    data = load_data()

    for client in data["clients"]:
        if client["id"] == str(client_id):
            return client.get("cart", [])

    return None


def get_cart_keyboard(message):
    markup = types.InlineKeyboardMarkup()

    cart = get_cart(message.chat.id)

    if cart is not None:
        for item in cart:
            item_button = types.InlineKeyboardButton(f'{item[0]} x{item[1]}', callback_data = f'item_cart_{cart.index(item)}_name')
            plus_button = types.InlineKeyboardButton("+", callback_data = f'item_cart_{cart.index(item)}_plus')
            minus_button = types.InlineKeyboardButton("-", callback_data = f'item_cart_{cart.index(item)}_minus')
            markup.add(minus_button, item_button, plus_button)

    return markup

def add_item(client_id, item):
    data = load_data()
    client_id = str(client_id)
    
    client_found = False
    for client in data["clients"]:
        if client["id"] == client_id:
            client_found = True
            if "cart" not in client:
                client["cart"] = []
            
            item_found = False
            for cart_item in client["cart"]:
                if cart_item[0] == item["name"]:
                    cart_item[1] += 1
                    item_found = True
                    break
            
            if not item_found:
                client["cart"].append([item["name"], 1])
            break
    
    if not client_found:
        data["clients"].append({
            "id": client_id,
            "cart": [[item["name"], 1]]
        })
    
    save_data(data)

def remove_item(client_id, item_index):
    data = load_data()
    client_id = str(client_id)
    
    for client in data["clients"]:
        if client["id"] == client_id and "cart" in client:
            if 0 <= item_index < len(client["cart"]):
                client["cart"][item_index][1] -= 1
                
                if client["cart"][item_index][1] <= 0:
                    client["cart"].pop(item_index)
                
                save_data(data)
                return True
    return False

def increase_item(client_id, item_index):
    data = load_data()
    client_id = str(client_id)
    
    for client in data["clients"]:
        if client["id"] == client_id and "cart" in client:
            if 0 <= item_index < len(client["cart"]):
                client["cart"][item_index][1] += 1
                save_data(data)
                return True
    return False

def is_valid_phone(phone):
    return phone.replace('+', '').replace(' ', '').isdigit()

def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    return {"clients": []}

def save_data(data):
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

@bot.message_handler(commands=["start"])
def handle_start(message: telebot.types.Message):
    bot.send_message(message.chat.id, "Привет!", reply_markup=main_menu())

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
    menu_btn = types.KeyboardButton("Меню 🍽️")
    bin_btn = types.KeyboardButton("Корзина 🛒")
    order_btn = types.KeyboardButton("Заказать")

    markup.add(menu_btn, bin_btn, order_btn)

    return markup

ITEMS_PER_PAGE = 4




def food_menu(page=0):
    markup = types.InlineKeyboardMarkup()

    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE

    for item in menu_items[start_index:end_index]:
        button = types.InlineKeyboardButton(f"{item['name']}: {item['price']}", callback_data = f'item_{menu_items.index(item)}')
        markup.add(button)

    if page > 0:
        markup.add(types.InlineKeyboardButton("<<", callback_data=f'page_{page-1}'))

    if end_index < len(menu_items):
        markup.add(types.InlineKeyboardButton(">>", callback_data=f'page_{page + 1}'))

    return markup


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    if call.data.startswith("page_"):
        _, page = call.data.split("_")
        markup = food_menu(int(page))
        bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text = 'Меню', reply_markup=markup)

    elif call.data.startswith("item_"):
        if "_cart_" in call.data:
            parts = call.data.split("_")
            item_index = int(parts[2])
            action = parts[3]
            cart = get_cart(call.message.chat.id)
            if cart and 0 <= item_index < len(cart):
                if action == "minus":
                    if remove_item(call.message.chat.id, item_index):
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text='Корзина',
                            reply_markup=get_cart_keyboard(call.message)
                        )
                elif action == "plus":
                    if increase_item(call.message.chat.id, item_index):
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text='Корзина',
                            reply_markup=get_cart_keyboard(call.message)
                        )
        else:
            _, chosen_item_index = call.data.split("_")
            chosen_item = menu_items[int(chosen_item_index)]
            add_item(call.message.chat.id, chosen_item)
            bot.send_message(call.message.chat.id, f"{chosen_item['name']} добавлено в корзину")



@bot.message_handler(commands=['add_info'])
def handle_add_name(message: types.Message):
    bot.send_message(message.chat.id, "введите имя")
    bot.register_next_step_handler_by_chat_id(message.chat.id, handle_add_number)

def handle_add_number(message: types.Message):
    bot.send_message(message.chat.id, "ваше имя сохранено")
    bot.send_message(message.chat.id, "введите номер телефона")
    name = message.text

    bot.register_next_step_handler_by_chat_id(message.chat.id, handle_end, name)

def handle_end(message: types.Message, name):
    number = message.text
    if not is_valid_phone(number):
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер телефона (только цифры)")
        bot.register_next_step_handler_by_chat_id(message.chat.id, handle_end, name)
        return

    user_id = str(message.from_user.id)
    
    data = load_data()
    
    user_exists = False
    for client in data["clients"]:
        if client["id"] == user_id:
            client["name"] = name
            client["phone"] = number
            client["cart"] = []
            user_exists = True
            break
    
    if not user_exists:
        data["clients"].append({
            "id": user_id,
            "name": name,
            "phone": number

        })
    
    save_data(data)
    
    bot.send_message(message.chat.id, f'ваш номер телефона: {number}, ваше имя: {name}')

def create_order(message):
    price = calculate_order(message.chat.id)

    if message.content_type == 'text':
        bot.send_message(message.chat.id, f'Вы выбрали адрес: {message.text}')
    if message.content_type == 'location':
        coord1 = message.location.latitude
        coord2 = message.location.longitude
        bot.send_message(message.chat.id, f'Вы выбрали местоположение: \n{coord1}\n{coord2}')

    bot.send_message(message.chat.id, f'Стоимость заказа: {price}')
    bot.send_message(message.chat.id, 'Доступна оплата только наличными курьеру')
    bot.send_message(message.chat.id, 'Заказ принят в работу', reply_markup = main_menu())





def calculate_order(client_id):
    total_price = 0
    cart = get_cart(client_id)
    for item in menu_items:
        for cart_item in cart:
            if item['name'] == cart_item[0]:
                price = int(item['price'].rstrip(' руб.')) * cart_item[1]

                total_price += price
    return total_price


@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.text == "Меню 🍽️":
        bot.reply_to(message, 'Вы открыли меню', reply_markup = food_menu())
    elif message.text == "Корзина 🛒":
        bot.reply_to(message, 'Вы открыли корзину', reply_markup = get_cart_keyboard(message))

    elif message.text == 'Заказать':
        cart = get_cart(message.chat.id)
        items = ''
        if cart is not None:
            for item in cart:
                items += f'\n{item[0]} x{item[1]}'
        bot.send_message(message.chat.id, f'Ваша корзина: {items}')


        keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
        agree_btn = types.KeyboardButton("Подтвердить ✅")
        cancel_btn = types.KeyboardButton("Отмена ❌")

        keyboard.add(agree_btn, cancel_btn)

        bot.send_message(message.chat.id, 'Подтвердите правильность заказа.', reply_markup = keyboard)

    elif message.text == 'Отмена ❌':
        bot.send_message(message.chat.id, 'Заказ не принят в работу. Вы можете изменить заказ.', reply_markup=main_menu())
    elif message.text == 'Подтвердить ✅':
        bot.send_message(message.chat.id, 'Введите адрес текстом или геометкой Telegram')

        bot.register_next_step_handler_by_chat_id(message.chat.id, create_order)

if __name__ == '__main__':
    bot.polling(none_stop=True)