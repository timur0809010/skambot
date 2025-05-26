import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import random   
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

BOT_TOKEN = "8141929022:AAGxzxJWnGQZQeshJEWoHd7WjSPAPRM3Tdg"
JSON_DB = "database.json"

#Спонсоры в таком формате ["@stargiverfree", "https://t.me/+sFYzeMzMVYs3Y2Uy @daillystar"]
Sponsor = ["@wowstarschannel", "@zalivchik01", "@zalivchik02", "@wowstarsviplaty" ]
#спонсоры с заявкам
Sponsorv2 = ["+YaM7XHKawJc3OGE6", "+Hoy2yDoQShM5YmQy", "+yVyBCnAJnUU1ZjIy", "+59YzQfSNVDAxNTVi", "+57DsOtzKo05hMGIy", "+57DsOtzKo05hMGIy", "+NcMqw3mSyuMwYTUy", "+KasEJbanfFRiOGFi", "giftsbattle_bot?startapp=ref_Zi5LuyDZ6"]
#Канал с выплатами
Withdraw_channel = ["@wowstarsviplaty"]
#Награда за реферала 
Referral_reward = 15
#ID Админа 
Admin = 8059249045
#ID Создателя
Developer = 8059249045
#Сума вывода
Withdraw_min = 15

bot = telebot.TeleBot(BOT_TOKEN)

def load_promo() -> List:
    if not os.path.exists("promo.json"):
        return []
    with open("promo.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_promo(data: List) -> None:
    with open("promo.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_task():
    try:
        with open("task.json", "r", encoding="utf-8") as f:
            tasks = json.load(f)
        
        current_time = datetime.now(timezone.utc)
        updated_tasks = []
        
        for task in tasks:
            try:
                task_time = datetime.strptime(task["time"], "%d-%m-%Y %H:%M").replace(tzinfo=timezone.utc)
                if task_time > current_time:
                    updated_tasks.append(task)
            except Exception as e:
                print(f"❌ Ошибка парсинга времени задания: {e}")
        
        if len(updated_tasks) < len(tasks):
            save_task(updated_tasks)
        
        return updated_tasks
    except FileNotFoundError:
        return []

def save_task(data: List) -> None:
    with open("task.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_db() -> Dict:
    if not os.path.exists(JSON_DB):
        return {}
    with open(JSON_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data: Dict) -> None:
    with open(JSON_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def check_subscription(user_id: int) -> bool:
    try:
        for sponsor in Sponsor:
            if "https://t.me/" in sponsor:
                parts = sponsor.split()
                if len(parts) > 1 and parts[1].startswith("@"):
                    channel = parts[1].replace("@", "")
                    status = bot.get_chat_member(f"@{channel}", user_id).status
                    if status not in ["member", "administrator", "creator"]:
                        return False
            elif "@" in sponsor:
                channel = sponsor.replace("@", "")
                status = bot.get_chat_member(f"@{channel}", user_id).status
                if status not in ["member", "administrator", "creator"]:
                    return False

        return True
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False

def main_menu(user_id: int) -> None:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("👤 Профиль", "🔗 Рефералы")
    markup.row("📌 Задания", "📝 Информация")
    bot.send_message(user_id, "🔹 Главное меню 🔹", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    db = load_db()

    if str(user_id) not in db:
        db[str(user_id)] = {
            "balance": 0,
            "referrals": [],
        }
        save_db(db)

    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]
        if referrer_id != str(user_id) and referrer_id in db:
            if 'pending_referral' not in db[str(user_id)]:
                db[str(user_id)]['pending_referral'] = referrer_id
                save_db(db)

    # Объединяем обязательные и необязательные спонсоры
    all_sponsors = [{"src": s, "required": True} for s in Sponsor] + [{"src": s, "required": False} for s in Sponsorv2]
    random.shuffle(all_sponsors)

    markup = InlineKeyboardMarkup()

    for sponsor in all_sponsors:
        s = sponsor["src"]
        required = sponsor["required"]

        if s.startswith("http") and " " in s:
            url, username = s.split()
        else:
            username = s
            url = f"https://t.me/{username.replace('@', '')}"

        markup.add(InlineKeyboardButton("Подписаться", url=url))

    # Проверка подписки, если есть обязательные
    if not check_subscription(user_id):
        markup.add(InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
        bot.send_message(user_id, "📢 Подпишитесь на спонсоров, чтобы продолжить:", reply_markup=markup)
    else:
        process_referral(user_id, db)
        main_menu(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    user_id = call.from_user.id
    db = load_db()
    
    if check_subscription(user_id):
        process_referral(user_id, db)
        main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Вы не подписаны на всех спонсоров!")
        
def process_referral(user_id, db):
    if 'pending_referral' in db.get(str(user_id), {}):
        referrer_id = db[str(user_id)]['pending_referral']
        if referrer_id in db and str(user_id) not in db[referrer_id]["referrals"]:
            db[referrer_id]["referrals"].append(str(user_id))
            db[referrer_id]["balance"] += Referral_reward
            del db[str(user_id)]['pending_referral']
            save_db(db)
            try:
                username = bot.get_chat(user_id).username
                bot.send_message(referrer_id, f"🎉 Новый реферал! @{username} (ID: {user_id})")
            except:
                pass

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    user_id = call.from_user.id
    db = load_db()
    
    if check_subscription(user_id):
        process_referral(user_id, db)
        main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Вы не подписаны на всех спонсоров!")

def process_referral(user_id, db):
    if 'pending_referral' in db.get(str(user_id), {}):
        referrer_id = db[str(user_id)]['pending_referral']
        if referrer_id in db and str(user_id) not in db[referrer_id]["referrals"]:
            db[referrer_id]["referrals"].append(str(user_id))
            db[referrer_id]["balance"] += Referral_reward
            del db[str(user_id)]['pending_referral']
            save_db(db)
            try:
                username = bot.get_chat(user_id).username
                bot.send_message(referrer_id, f"🎉 Новый реферал! @{username} (ID: {user_id})")
            except:
                pass

@bot.message_handler(func=lambda msg: msg.text == "👤 Профиль")
def profile(message):
    user_id = message.from_user.id
    db = load_db()
    user_data = db.get(str(user_id), {"balance": 0, "task": [], "referrals": []})

    text = (
        f"👤 *Ваш профиль*\n"
        f"🧑‍💻 *ID*: {user_id}\n"
        f"💸 *Юзернейм*: @{message.from_user.username}\n"
        f"⭐ *Баланс*: {user_data['balance']:.2f} stars\n"
        f"🔗 *Рефералов*: {len(user_data['referrals'])}"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Промокод", callback_data="promo"))
    markup.add(InlineKeyboardButton("💳 Вывести", callback_data="withdraw"))



    process_referral(user_id, db)
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")


@bot.message_handler(commands=['addpromo'])
def add_promo(message):
    user_id = message.from_user.id
    if user_id != Admin:
        bot.reply_to(message, "❌ Эта команда доступна только администратору!")
        return
    
    msg = bot.send_message(user_id, "Введите название промокода:")
    bot.register_next_step_handler(msg, process_add_promo_step1)

def process_add_promo_step1(message):
    promo_name = message.text.strip()
    msg = bot.send_message(message.from_user.id, "Введите количество активаций для промокода:")
    bot.register_next_step_handler(msg, lambda m: process_add_promo_step2(m, promo_name))

def process_add_promo_step2(message, promo_name):
    try:
        activations = int(message.text)
        msg = bot.send_message(message.from_user.id, "Введите награду (количество stars):")
        bot.register_next_step_handler(msg, lambda m: process_add_promo_step3(m, promo_name, activations))
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Некорректное число активаций! Введите целое число.")

def process_add_promo_step3(message, promo_name, activations):
    try:
        reward = float(message.text)
        promos = load_promo()
        
        if any(p.get("name") == promo_name for p in promos):
            bot.send_message(message.from_user.id, "❌ Промокод с таким именем уже существует!")
            return
        
        promos.append({
            "name": promo_name,
            "promo": promo_name.lower().replace(" ", "_"),
            "Active": activations,
            "Reward": reward,
            "Users": []
        })
        
        save_promo(promos)
        bot.send_message(message.from_user.id,
                       f"✅ Промокод успешно создан!\n"
                       f"🏷 Название: {promo_name}\n"
                       f"🔢 Код: {promo_name.lower().replace(' ', '_')}\n"
                       f"🔄 Активаций: {activations}\n"
                       f"⭐ Награда: {reward} stars")
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Некорректная сумма награды! Введите число.")

@bot.callback_query_handler(func=lambda call: call.data == "promo")
def promo_handler(call):
    user_id = call.from_user.id
    msg = bot.send_message(user_id, "Введите промокод:")
    bot.register_next_step_handler(msg, process_promo)

def process_promo(message):
    user_id = message.from_user.id
    promo_code = message.text.strip().lower().replace(" ", "_")
    promos = load_promo()
    db = load_db()
    
    found = False
    for promo in promos:
        if promo["promo"] == promo_code:
            found = True
            if str(user_id) in promo["Users"]:
                bot.send_message(user_id, "❌ Вы уже активировали этот промокод!")
                return
            
            if len(promo["Users"]) >= promo["Active"]:
                promos.remove(promo)
                save_promo(promos)
                bot.send_message(user_id, "❌ Лимит активаций этого промокода исчерпан!")
                return
            
            promo["Users"].append(str(user_id))
            reward = promo["Reward"]
            
            if str(user_id) not in db:
                db[str(user_id)] = {"balance": 0, "referrals": []}
            db[str(user_id)]["balance"] += reward
            
            save_db(db)
            save_promo(promos)
            
            remaining = promo["Active"] - len(promo["Users"])
            bot.send_message(user_id, 
                           f"✅ Промокод '{promo['name']}' активирован!\n"
                           f"🎁 Получено: {reward} stars\n"
                           f"🔄 Осталось активаций: {remaining}")
            
            if remaining <= 0:
                promos.remove(promo)
                save_promo(promos)
            return
    
    if not found:
        bot.send_message(user_id, "❌ Промокод не найден. Проверьте правильность ввода.")
        
@bot.message_handler(commands=['addtask'])
def add_task(message):
    user_id = message.from_user.id
    if user_id != Admin:
        bot.reply_to(message, "❌ Эта команда доступна только администратору!")
        return
    
    msg = bot.send_message(user_id, "🔹 Отправьте ссылку на задание (или @username канала):")
    bot.register_next_step_handler(msg, process_add_task_step1)

def process_add_task_step1(message):
    try:
        task_link = message.text.strip()
        msg = bot.send_message(message.from_user.id, 
                             "🔹 Теперь перешлите любое сообщение из канала для проверки подписки\n"
                             "(бот автоматически получит ID канала):")
        bot.register_next_step_handler(msg, lambda m: process_add_task_step2(m, task_link))
    except Exception as e:
        bot.send_message(message.from_user.id, f"❌ Ошибка: {str(e)}")

def process_add_task_step2(message, task_link):
    try:
        if message.forward_from_chat:
            if message.forward_from_chat.type == 'channel':
                channel_id = message.forward_from_chat.id
                channel_username = message.forward_from_chat.username
                channel_title = message.forward_from_chat.title
                
                channel_info = f"id:{channel_id}"
                bot.send_message(message.from_user.id, 
                               f"✅ Канал получен: {channel_title}\n"
                               f"ID: {channel_id}\n"
                               f"Username: @{channel_username if channel_username else 'нет'}")
                
                msg = bot.send_message(message.from_user.id, 
                                    "⏳ Введите время окончания задания (ДД-ММ-ГГГГ ЧЧ:ММ UTC):")
                bot.register_next_step_handler(msg, lambda m: process_add_task_step3(m, task_link, channel_info))
            else:
                bot.send_message(message.from_user.id, "❌ Нужно переслать сообщение именно из канала!")
        else:
            bot.send_message(message.from_user.id, "❌ Нужно переслать сообщение из канала!")
    except Exception as e:
        bot.send_message(message.from_user.id, f"❌ Ошибка: {str(e)}")

def process_add_task_step3(message, task_link, channel_info):
    try:
        time_str = message.text.strip()
        datetime.strptime(time_str, "%d-%m-%Y %H:%M")
        
        msg = bot.send_message(message.from_user.id, "💰 Введите награду (количество stars):")
        bot.register_next_step_handler(msg, lambda m: process_add_task_step4(m, task_link, channel_info, time_str))
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Некорректный формат времени! Используйте ДД-ММ-ГГГГ ЧЧ:ММ")
    except Exception as e:
        bot.send_message(message.from_user.id, f"❌ Ошибка: {str(e)}")

def process_add_task_step4(message, task_link, channel_info, time_str):
    try:
        reward = float(message.text)
        tasks = load_task()
        
        if any(t["task"] == task_link for t in tasks):
            bot.send_message(message.from_user.id, "❌ Задание с такой ссылкой уже существует!")
            return
        
        tasks.append({
            "task": task_link,
            "Examination": channel_info,
            "time": time_str,
            "Reward": reward,
            "Users": []
        })
        
        save_task(tasks)
        bot.send_message(message.from_user.id, 
                       f"✅ Задание успешно добавлено!\n"
                       f"🔗 Ссылка: {task_link}\n"
                       f"📢 Канал: {channel_info}\n"
                       f"⏳ До: {time_str}\n"
                       f"💰 Награда: {reward} stars")
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Некорректная сумма награды! Введите число.")
    except Exception as e:
        bot.send_message(message.from_user.id, f"❌ Ошибка при сохранении задания: {str(e)}")

@bot.message_handler(func=lambda msg: msg.text == "📌 Задания")
def tasks_handler(message):
    user_id = message.from_user.id
    tasks = load_task()
    user_tasks = [t for t in tasks if str(user_id) not in t["Users"]]
    
    if not user_tasks:
        bot.send_message(user_id, "❌ На данный момент нет доступных заданий!")
        return
    
    show_task(user_id, user_tasks, 0)

def show_task(user_id, tasks, index):
    task = tasks[index]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 Выполнить задание", url=task["task"]))
    markup.add(InlineKeyboardButton("✅ Проверить", callback_data=f"check_task_{index}"))
    
    if len(tasks) > 1:
        if index < len(tasks) - 1:
            markup.add(InlineKeyboardButton("➡️ Далее", callback_data=f"next_task_{index + 1}"))
        else:
            markup.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_task_{index - 1}"))
    
    bot.send_message(user_id, f"📌 Задание {index + 1}/{len(tasks)}\n\nПодпишитесь на канал и нажмите проверить:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(("check_task_", "next_task_", "prev_task_")))
def task_actions(call):
    user_id = call.from_user.id
    action, index = call.data.split("_")[0], int(call.data.split("_")[-1])
    tasks = load_task()
    user_tasks = [t for t in tasks if str(user_id) not in t["Users"]]
    
    if action == "check":
        task = user_tasks[index]
        if check_subscription(user_id, task["Examination"]):
            tasks = load_task()
            for t in tasks:
                if t["task"] == task["task"]:
                    t["Users"].append(str(user_id))
                    save_task(tasks)
                    db = load_db()
                    db[str(user_id)]["balance"] += task["Reward"]
                    save_db(db)
                    bot.send_message(user_id, f"✅ Задание выполнено! Получено {task['Reward']} stars")
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    break
        else:
            bot.answer_callback_query(call.id, "❌ Вы не подписаны на канал!")
    elif action in ["next", "prev"]:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_task(user_id, user_tasks, index)

def check_task(user_id: int, channel_info: str) -> bool:
    try:
        if channel_info.startswith("id:"):
            chat_id = int(channel_info[3:])
        else:
            print(f"❌ Ошибка: ожидался формат id:123456, но получено {channel_info}")
            return False

        try:
            status = bot.get_chat_member(chat_id, user_id).status
            return status in ["member", "administrator", "creator"]
        except Exception as e:
            print(f"Ошибка получения статуса пользователя в канале ({chat_id}): {e}")
            return False
    except Exception as e:
        print(f"Общая ошибка в check_task: {e}")
        return False

@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    user_id = str(call.from_user.id)
    db = load_db()
    balance = db.get(user_id, {}).get("balance", 0)
    referrals = db.get(user_id, {}).get("referrals", [])

    if len(referrals) < 10:
        bot.answer_callback_query(call.id, "❌ Для вывода нужно минимум 10 рефералов!")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("15 stars 🧸💝", callback_data="withdraw_15"),
        InlineKeyboardButton("25 stars 🌹🎁", callback_data="withdraw_25"),
        InlineKeyboardButton("50 stars 💐🎂🚀🍾", callback_data="withdraw_50"),
        InlineKeyboardButton("100 stars 💎💍🏆", callback_data="withdraw_100")
    )
    
    bot.send_message(
        chat_id=call.message.chat.id,
        text=f"💰 Ваш баланс: {balance:.2f} stars\n\nВыберите сумму для вывода:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_"))
def process_withdraw(call):
    user_id = str(call.from_user.id)
    db = load_db()
    user_data = db.get(user_id, {})
    balance = user_data.get("balance", 0)
    referrals = user_data.get("referrals", [])

    if len(referrals) < 10:
        bot.answer_callback_query(call.id, "❌ Для вывода нужно минимум 10 рефералов!")
        return

    amount = int(call.data.split("_")[1])

    if balance < amount:
        bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Ваш баланс: {balance:.2f} stars")
        return

    db[user_id]["balance"] -= amount
    save_db(db)

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{user_id}_{amount}"),
        InlineKeyboardButton("👤 Профиль", url=f"tg://user?id={user_id}")
    )
    markup.row(InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}_{amount}"))

    admin_text = (
        "📌 *Новая заявка на вывод*\n"
        f"▫️ *ID*: `{user_id}`\n"
        f"▫️ *Юзернейм*: @{call.from_user.username}\n"
        f"▫️ *Баланс*: `{balance:.2f} stars`\n"
        f"▫️ *Рефералов*: `{len(referrals)}`\n"
        f"▫️ *Сумма*: `{amount:.2f} stars`"
    )
    user_text = (
        f"📌 *Вы отправили заявку на вывод {amount:.2f} stars, с вашего баланса списано {amount:.2f} звёзд. Ожидайте вывода.*"
    )
    bot.send_message(Admin, admin_text, reply_markup=markup, parse_mode="Markdown")
    bot.send_message(call.from_user.id, user_text, parse_mode="Markdown")
    bot.answer_callback_query(call.id, f"✅ Заявка на вывод {amount} stars отправлена!")


@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def admin_actions(call):
    parts = call.data.split("_")
    action = parts[0]
    user_id = parts[1]
    amount = float(parts[2])

    db = load_db()

    if action == "approve":
        bot.send_message(int(user_id), f"✅ Ваша заявка на вывод {amount} stars одобрена!")
        bot.answer_callback_query(call.id, "✅ Заявка одобрена!")
    elif action == "reject":
        db[user_id]["balance"] += amount
        save_db(db)
        bot.send_message(int(user_id), f"❌ Ваша заявка на вывод {amount} stars отклонена!")
        bot.answer_callback_query(call.id, "❌ Заявка отклонена!")


@bot.message_handler(func=lambda msg: msg.text == "📝 Информация")
def bot_info(message):
    user_id = message.from_user.id
    db = load_db()
    
    total_users = len([uid for uid in db if uid.isdigit()])
    total_balance = sum(user_data.get("balance", 0) for uid, user_data in db.items() if uid.isdigit())


    
    text = (
        "📊 *Информация о боте*\n\n"
        f"👥 Всего пользователей: `{total_users}`\n"
        f"💰 Общий баланс: `{total_balance:.2f} stars`\n\n"
        "ℹ️ Дополнительная информация: \n \n"
        "❤️‍🔥 Не писать разработчику по поводу выплат, пишите если хотите такого же бота."
    )

    
    if not check_subscription(user_id):
        markup = InlineKeyboardMarkup()
        for sponsor in Sponsor:
            if "https://t.me/" in sponsor:
                parts = sponsor.split()
                if len(parts) > 1 and parts[1].startswith("@"):
                    url = parts[0]
                    btn_text = f"Подписаться {parts[1]}"
                    markup.add(InlineKeyboardButton(btn_text, url=url))
            else:
                markup.add(InlineKeyboardButton(f"Подписаться {sponsor}", url=f"https://t.me/{sponsor.replace('@', '')}"))
        markup.add(InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
        bot.send_message(user_id, "📢 Подпишитесь на спонсоров, чтобы продолжить:", reply_markup=markup)
    else:
        process_referral(user_id, db)
        
        markup = InlineKeyboardMarkup()
        main_menu(user_id)
        buttons_row = []
        if Developer:
            buttons_row.append(InlineKeyboardButton("👨‍💻 Разработчик", url=f"tg://user?id={Developer}"))
        if Admin:
            buttons_row.append(InlineKeyboardButton("👨‍⚖️ Админ", url=f"tg://user?id={Admin}"))
        
        if buttons_row:
            markup.row(*buttons_row)
        buttons_row = []

        if Withdraw_channel and Withdraw_channel[0]:
            buttons_row.append(InlineKeyboardButton("💸 Выплаты", url=f"https://t.me/{Withdraw_channel[0].replace('@', '')}"))

        buttons_row.append(InlineKeyboardButton("🏆 Топ рефералов", callback_data="top_referrals"))
        
        markup.row(*buttons_row)
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")
        
        
        

@bot.callback_query_handler(func=lambda call: call.data == "top_referrals")
def show_top_referrals(call):
    user_id = call.from_user.id
    db = load_db()
    
    referrals_list = []
    for user_id_str, user_data in db.items():
        if "referrals" in user_data and user_data["referrals"]:
            try:
                user = bot.get_chat(int(user_id_str))
                username = f"@{user.username}" if user.username else f"{user.first_name or 'Пользователь'}"
            except:
                username = f"ID: {user_id_str}"
            referrals_list.append((username, len(user_data["referrals"])))
    
    referrals_list.sort(key=lambda x: x[1], reverse=True)
    
    top_referrals = referrals_list[:5]
    
    if top_referrals:
        text = "🏆 *Топ 5 по рефералам*\n\n"
        for i, (username, count) in enumerate(top_referrals, 1):
            text += f"{i}. {username} - {count} реф.\n"
    else:
        text = "😔 Пока нет данных о рефералах"
    
    bot.send_message(
        chat_id=call.message.chat.id,
        text=text,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda msg: msg.text == "🔗 Рефералы")
def partners(message):
    user_id = message.from_user.id
    db = load_db()
    ref_count = len(db.get(str(user_id), {}).get("referrals", []))

    text = (
        "🤝 *Реферальная Програма*\n"
        f"💸 Приглашено: {ref_count}\n"
        f"⭐ Награда за реферала: {Referral_reward:.2f} stars\n\n"
        f"🔗 Ваша ссылка:\n`https://t.me/{bot.get_me().username}?start={user_id}`"
    )
    # Объединяем обязательные и необязательные спонсоры
    all_sponsors = [{"src": s, "required": True} for s in Sponsor] + [{"src": s, "required": False} for s in Sponsorv2]
    random.shuffle(all_sponsors)

    markup = InlineKeyboardMarkup()

    for sponsor in all_sponsors:
        s = sponsor["src"]
        required = sponsor["required"]

        if s.startswith("http") and " " in s:
            url, username = s.split()
        else:
            username = s
            url = f"https://t.me/{username.replace('@', '')}"

        markup.add(InlineKeyboardButton("Подписаться", url=url))

    # Проверка подписки, если есть обязательные
    if not check_subscription(user_id):
        markup.add(InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
        bot.send_message(user_id, "📢 Подпишитесь на спонсоров, чтобы продолжить:", reply_markup=markup)
    else:
        process_referral(user_id, db)
        main_menu(user_id)
        bot.send_message(user_id, text, parse_mode="Markdown")

pending_post = {}

@bot.message_handler(commands=['post'])
def handle_post_command(message):
    user_id = message.from_user.id
    if user_id != Admin:
        bot.reply_to(message, "❌ Эта команда доступна только администратору!")
        return
    
    msg = bot.reply_to(message, "📢 Отправьте сообщение для рассылки (текст, фото или фото с текстом):")
    bot.register_next_step_handler(msg, process_post_content)

def process_post_content(message):
    user_id = message.from_user.id
    if user_id != Admin:
        return
    
    pending_post['content'] = message
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Отправить", callback_data="send_post"),
        InlineKeyboardButton("❌ Отменить", callback_data="cancel_post")
    )
    
    if message.content_type == 'text':
        bot.send_message(user_id, f"📝 Ваше сообщение для рассылки:\n\n{message.text}\n\nПодтвердите отправку:", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "", 
                      reply_markup=markup)
    elif message.content_type == 'document':
        bot.send_document(user_id, message.document.file_id, caption=message.caption or "", 
                         reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['send_post', 'cancel_post'])
def handle_post_confirmation(call):
    if call.from_user.id != Admin:
        bot.answer_callback_query(call.id, "❌ Только администратор может подтверждать рассылку!")
        return
    
    if call.data == 'cancel_post':
        bot.edit_message_text(chat_id=call.message.chat.id, 
                            message_id=call.message.message_id, 
                            text="❌ Рассылка отменена!")
        pending_post.clear()
        return
    
    db = load_db()
    total_users = len(db)
    sent_count = 0
    
    bot.edit_message_text(chat_id=call.message.chat.id, 
                         message_id=call.message.message_id, 
                         text="⏳ Начинаю рассылку...")
    
    message = pending_post['content']
    
    for user_id_str in db.keys():
        try:
            if message.content_type == 'text':
                bot.send_message(user_id_str, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(user_id_str, message.photo[-1].file_id, caption=message.caption or "")
            elif message.content_type == 'document':
                bot.send_document(user_id_str, message.document.file_id, caption=message.caption or "")
            sent_count += 1
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id_str}: {e}")
    
    bot.send_message(Admin, f"✅ Рассылка завершена!\nОтправлено: {sent_count}/{total_users} пользователей")
    pending_post.clear()


@bot.message_handler(commands=["set_balance"])
def set_balance(message):
    if message.from_user.id != Admin:
        return

    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "❗ Использование: `/set_balance <user_id> <сумма>`", parse_mode="Markdown")
        return

    user_id, new_balance = parts[1], parts[2]
    try:
        new_balance = float(new_balance)
    except ValueError:
        bot.reply_to(message, "❗ Сумма должна быть числом.", parse_mode="Markdown")
        return

    db = load_db()

    if user_id in db:
        db[user_id]["balance"] = new_balance
        save_db(db)
        bot.reply_to(message, f"✅ Баланс пользователя `{user_id}` обновлён: {new_balance}⭐", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"❌ Пользователь `{user_id}` не найден в базе.", parse_mode="Markdown")


@bot.message_handler(commands=['dump'])
def dump_db(message):
    if message.from_user.id != Admin: return  # Только админ
    db = load_db()
    bot.send_document(message.chat.id, open(JSON_DB, 'rb'))


@bot.message_handler(commands=['reward'])
def set_reward(message):
    global Referral_reward
    if message.from_user.id != Admin:
        return bot.reply_to(message, "⛔ У вас нет доступа к этой команде.")
    
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            return bot.reply_to(message, "❗ Использование: /reward 1.5")

        new_reward = float(parts[1])
        Referral_reward = new_reward
        bot.reply_to(message, f"✅ Награда за реферала обновлена: {Referral_reward} ⭐")
    except ValueError:
        bot.reply_to(message, "❌ Введите корректное число. Пример: `/reward 1.5`", parse_mode="Markdown")



if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling()
