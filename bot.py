import telebot
from telebot import types
from config import token
from models import Product, Category, Cart, Order
from app import db
from dataclasses import dataclass
from redis_cart import get_the_whole_cart_user, get_product_in_cart, add_product_in_cart, empty_the_cart,\
    delete_product_in_cart, plus_product_in_cart, minus_product_in_cart


bot = telebot.TeleBot(f'{token}')
p_image = ['🍕', '🍣', '🥗', '🍤']


@bot.message_handler(commands=['start'])
def start(message):
    """Обработка команды 'start'"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_menu = types.KeyboardButton('🍽 Меню')
    btn_cart = types.KeyboardButton('🗑 Корзина')
    btn_news = types.KeyboardButton('📬 Новости')
    btn_about_us = types.KeyboardButton('📜 О нас')
    markup.add(btn_menu, btn_cart, btn_news, btn_about_us)
    bot.send_message(message.chat.id, '<strong>Добро пожаловать в наш магазин!</strong>', parse_mode='html',
                     reply_markup=markup)


@bot.message_handler(content_types='text')
def menu(message):
    if message:
        if message.text == '🍽 Меню':
            # обработка кнопки "Меню"
            markup = types.InlineKeyboardMarkup(row_width=2)
            cat = Category.query.all()
            for i in range(len(cat)):
                category = Category.query.filter(Category.id == cat[i].id).first()
                btn = types.InlineKeyboardButton(f'{p_image[i]}   {cat[i]} ({len(category.Products.all())})',
                                                 callback_data=f'{cat[i]}')
                markup.add(btn)
            bot.send_message(message.chat.id, '<b>Выберите категорию:</b>', parse_mode='html', reply_markup=markup)

        if message.text == '🗑 Корзина':
            # обработка кнопки "Корзина"
            if not get_the_whole_cart_user(f'order_user_id{message.chat.id}'):
                # если корзина пустая
                cart_markup = types.InlineKeyboardMarkup(row_width=2)
                btn = types.InlineKeyboardButton('⬅️  В каталог', callback_data='back')
                cart_markup.add(btn)
                bot.send_message(message.chat.id, '🙁  Ваша корзина пуста', reply_markup=cart_markup)
            else:
                # если в корзине есть продукты
                products = get_the_whole_cart_user(f'order_user_id{message.chat.id}')
                if len(products) > 0:
                    for product_id in products:
                        product_coast = get_product_in_cart(f'order_user_id{message.chat.id}', str(product_id))
                        product = Product.query.filter(Product.id == product_id).first()
                        buttons = types.InlineKeyboardMarkup(row_width=4)
                        btn_del = types.InlineKeyboardButton('❌', callback_data=f'delete{str(product_id)}')
                        btn_down = types.InlineKeyboardButton('⬇️', callback_data=f'down{product_id}')
                        btn_product = types.InlineKeyboardButton(f'{product_coast}', callback_data='produuuuct')
                        btn_up = types.InlineKeyboardButton('⬆', callback_data=f'up{product_id}')
                        buttons.add(btn_del, btn_down, btn_product, btn_up)
                        bot.send_message(message.chat.id,
                                         f'У вас в корзине - {product.name}, стоимость {product.price}',
                                         reply_markup=buttons)
                    bot.send_message(message.chat.id, text='Что делаем?',
                                     reply_markup=get_two_buttons('Оформить заказ', 'sc', 'Очистить корзину', 'del'))

        if message.text == '📜 О нас':
            # обработка кнопки "О нас"
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_edit = types.InlineKeyboardButton('Редактировать', callback_data='edit_message')
            markup.add(btn_edit)
            bot.send_message(message.chat.id, text='Тестовое сообщение', reply_markup=markup)


def get_two_buttons(name_first_btn, callback_data1, name_second_btn, callback_data2):
    """Возвращает две InlineKeyboardButton"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_first = types.InlineKeyboardButton(f'{name_first_btn}', callback_data=f'{callback_data1}')
    btn_second = types.InlineKeyboardButton(f'{name_second_btn}', callback_data=f'{callback_data2}')
    markup.add(btn_first, btn_second)
    return markup


def get_product(call, product_cat):
    """Отобращает продукты в переданной категории"""
    category = Category.query.filter(Category.id == product_cat).first()
    product = category.Products.all()[0:1]

    for key in product:
        user_session = call.message.chat.id
        cart = get_the_whole_cart_user(f'order_user_id{user_session}')
        if key.id in cart:
            # Если продукт добавлен в корзину, кнопка "Добавить в корзину" заменяется на "Удалить из корзины"
            pic = open(f'static/img/{key.image}', 'rb')
            bot.send_message(call.message.chat.id, key.name)
            bot.send_photo(call.message.chat.id, pic,
                           reply_markup=get_two_buttons('❌ Удалить из корзины',
                                                        f'delete{key.id}',
                                                        '⬅️ Назад',
                                                        'back'))

        else:
            # Если продукт не добавлен в корзину
            pic = open(f'static/img/{key.image}', 'rb')
            bot.send_message(call.message.chat.id, key.name)
            bot.send_photo(call.message.chat.id, pic, reply_markup=get_two_buttons('🛍 В корзину',
                                                                                   key.id,
                                                                                   '⬅️ Назад',
                                                                                   'back'))


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        products = [str(name.id) for name in Product.query.all()]
        # Обработка кнопки "пицца"
        if call.data == 'Пицца':
            category = Category.query.filter(Category.id == 1).first()
            bot.send_message(call.message.chat.id, '<b>Выберите пиццу:</b>', parse_mode='html')
            get_product(call, 1)

        if call.data == 'Роллы':
            # Обработка кнопки "роллы"
            bot.send_message(call.message.chat.id, '<b>Выберите ролл:</b>', parse_mode='html')
            get_product(call, 4)

        if call.data == 'Салаты':
            # Обработка кнопки "салаты"
            bot.send_message(call.message.chat.id, '<b>Выберите салат:</b>', parse_mode='html')
            get_product(call, 3)

        if call.data == 'Закуски':
            # Обработка кнопки "закуски"
            bot.send_message(call.message.chat.id, '<b>Выберите закуски:</b>', parse_mode='html')
            get_product(call, 2)

        if call.data == 'back':
            # Обработка кнопки "Назад"
            markup = types.InlineKeyboardMarkup(row_width=2)
            cat = Category.query.all()
            for i in range(len(cat)):
                category = Category.query.filter(Category.id == cat[i].id).first()
                btn = types.InlineKeyboardButton(f'{p_image[i]}  {cat[i]} ({len(category.Products.all())})',
                                                 callback_data=f'{cat[i]}')
                markup.add(btn)
            bot.send_message(call.message.chat.id, '<b>Выберите категорию:</b>', parse_mode='html', reply_markup=markup)

        if call.data in products:
            # Добавление продукта в корзину
            try:
                appended_product_id = (Product.query.filter(Product.id == call.data).first())
                add_product_in_cart(f'order_user_id{call.message.chat.id}', appended_product_id.id)

                bot.answer_callback_query(callback_query_id=call.id, text='Добавлено в корзину')
                bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                              reply_markup=get_two_buttons('❌ Удалить из корзины',
                                                                           f'delete{appended_product_id.id}',
                                                                           '⬅️ Назад',
                                                                           'back'))
            except KeyError:
                print('ЧТо то пошло не так')

        if call.data == 'del':
            # Обработка кнопки "Очистить корзину"
            cart_markup = types.InlineKeyboardMarkup(row_width=2)
            btn = types.InlineKeyboardButton('🥢 В каталог', callback_data='back')
            cart_markup.add(btn)
            empty_the_cart(f'order_user_id{call.message.chat.id}')
            bot.send_message(call.message.chat.id, '🙁 Корзина пуста', reply_markup=cart_markup)

        if call.data == 'sc':
            # Обработка кнопки "Оформить заказ"
            name = 'denis'
            phone = '1234'
            address = '30 let WLKSM'
            payment = 'наличные'
            # pr = [product_id for product_id in sessions[f'{call.message.chat.id}']['product_id']]
            # products_id = [Product.query.filter(Product.name == pr[i]).first().id for i in range(len(pr))]
            products_coast = 1
            order = Order(user_name=name, phone=phone, address=address, payment=payment)
            db.session.add(order)
            db.session.commit()
            # for i in range(len(products_id)):
            #     cart = Cart(order_id=order.id, product_id=products_id[i], count=products_coast)
            #     db.session.add(cart)
            #     db.session.commit()
            #     print('Успешно')
            # bot.send_message(call.message.chat.id, 'Успешно, ждите звонка оператора')

        if call.data.startswith('down'):
            # обработка кнопки "вниз"
            pr_id = int(call.data[4:])
            pr = get_product_in_cart(f'order_user_id{call.message.chat.id}', f'{pr_id}')
            if pr > 0:
                buttons = types.InlineKeyboardMarkup(row_width=4)
                btn_del = types.InlineKeyboardButton('❌', callback_data=f'deleasdfteasdafa')
                btn_down = types.InlineKeyboardButton('⬇️', callback_data=f'down{pr_id}')
                btn_product = types.InlineKeyboardButton(
                    get_product_in_cart(f'order_user_id{call.message.chat.id}', f'{pr_id}'),
                    callback_data='produuuuct')
                minus_product_in_cart(f'order_user_id{call.message.chat.id}', str(pr_id))
                btn_up = types.InlineKeyboardButton('⬆', callback_data=f'up{pr_id}')
                buttons.add(btn_del, btn_down, btn_product, btn_up)
                bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                              reply_markup=buttons)
            else:
                pass

        if call.data.startswith('up'):
            # обработка кнопки "вверх"
            pr_id = int(call.data[2:])
            plus_product_in_cart(f'order_user_id{call.message.chat.id}', str(pr_id))
            buttons = types.InlineKeyboardMarkup(row_width=4)
            btn_del = types.InlineKeyboardButton('❌', callback_data=f'deleasdfteasdafa')
            btn_down = types.InlineKeyboardButton('⬇️',
                                                  callback_data=f'down{pr_id}')
            btn_product = types.InlineKeyboardButton(
                get_product_in_cart(f'order_user_id{call.message.chat.id}', f'{pr_id}'), callback_data='produuuuct')
            btn_up = types.InlineKeyboardButton('⬆', callback_data=f'up{pr_id}')
            buttons.add(btn_del, btn_down, btn_product, btn_up)
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=buttons)

        if call.data.startswith('delete'):
            # Обработка кнопки "Удалить товар из корзины ❌"
            pr_id = int(call.data[6:])
            delete_product_in_cart(f'order_user_id{call.message.chat.id}', f'{pr_id}')

            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=get_two_buttons('🛍 Добавить в корзину',
                                                                       pr_id,
                                                                       '⬅️ Назад',
                                                                       'back'))


if __name__ == '__main__':
    print('Бот запущен')
    bot.infinity_polling()
