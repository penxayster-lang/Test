# -*- coding: utf-8 -*-
import dotenv
import os
import re
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
import requests
import random
import json
from cachetools import TTLCache

massage = "Привет! Я Бофасний - бот, определяющий фишинговые ссылки. Пришли мне ссылку и я проверю её по своей базе ссылок. А также я могу дать совет по безопасному использованию информационных технологий. "
ad_conteiner = ["! Включите двухфакторную аутентификацию (2FA) везде, где это возможно!\n2FA добавляет дополнительный уровень защиты к вашим учетным записям. Даже если кто-то узнает ваш пароль, ему потребуется второй фактор (например, код из SMS или приложения-аутентификатора) для входа в систему. Это значительно снижает риск взлома.",
                "! Используйте надежные и уникальные пароли для каждой учетной записи!\nНадежный пароль должен быть длинным (не менее 12 символов) и содержать случайную комбинацию букв верхнего и нижнего регистра, цифр и символов. Использование уникальных паролей для каждой учетной записи предотвращает компрометацию нескольких учетных записей, если одна из них будет взломана.",
                "! Используйте надежное антивирусное ПО и регулярно сканируйте свою систему\nРегулярное сканирование системы позволяет обнаруживать и удалять вредоносные программы, прежде чем они смогут нанести ущерб.",
                "! Загружайте приложения только из официальных источников!\nСкачивание программ с неизвестных сайтов увеличивает риск заражения устройства.",
                "! Остерегайтесь общественного Wi-Fi!\nСеть Wi-Fi может быть незащищённой, и подключение к общедоступному Wi-Fi рискует передать данные злоумышленникам.",
                "! Ограничьте информацию, которой вы делитесь в социальных сетях!\nНе делитесь личной информацией (например, датой рождения, адресом, номером телефона) в социальных сетях, так как она может быть использована для кражи личных данных или других злонамеренных целей.",
                "!Не открывайте подозрительные файлы и архивы из сообщений.\n Даже если файл пришёл “от знакомого”, его аккаунт мог быть взломан. Особенно опасны файлы с расширениями .exe, .js, .bat, а также архивы .zip/.rar с паролем.",
                "!Регулярно обновляйте систему и приложения.\n Обновления закрывают уязвимости, которыми часто пользуются злоумышленники. Включите автоматические обновления, если есть такая возможность.",
                "!Не сообщайте коды подтверждения и одноразовые пароли никому.\n Сотрудники банков и техподдержки не имеют права просить коды из SMS или приложений. Если кто-то просит такой код — это почти наверняка мошенник."]

async def advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    random_advice = random.choice(ad_conteiner)
    await update.message.reply_text(random_advice)

def extract_url(text: str):
    if not text:
        return None
    url_found = re.search(r"https?://\S+", text)
    if not url_found:
        return None
    url = url_found.group(0)
    url = url.rstrip('.,;:!?)"]}>\'')
    return url



async def check_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите полную ссылку (Убедитесь в правильности написания и в отсутствии лишних знаков)"
    )
    context.user_data["job"] = True

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("job", False):
        await update.message.reply_text("Используй команды для взаимодействия со мной")
        return None
    urlx = update.message.text.strip()

    extracted_url = extract_url(urlx)
    if not extracted_url:
        await update.message.reply_text(
            "Я не нашёл ссылку в сообщении. Пришли ссылку, которая начинается с http:// или https://")
        return None
    urlx = extracted_url

    url_cache = context.application.bot_data["url_cache"]
    cached = url_cache.get(urlx)
    if cached is not None:
        json_response = cached
    else:
        urlhaus_api = "https://urlhaus-api.abuse.ch/v1/url/"
        headers = {"Auth-Key": API_KEY}
        data = {"url": urlx}
        try:
            response = requests.post(urlhaus_api, headers=headers, data=data, timeout=20)
            response.raise_for_status()
            json_response = response.json()


            if json_response.get("query_status") in ("ok", "no_results"):
                url_cache[urlx] = json_response

        # Отправка пользователю сообщения об ошибке:
        except requests.exceptions.RequestException:
            await update.message.reply_text("Ошибка подключения к URLhaus")
            context.user_data["job"] = False
            return None
        except json.JSONDecodeError:
            await update.message.reply_text("Ошибка обработки ответа от URLhaus")
            context.user_data["job"] = False
            return None

    if json_response.get("query_status") == "ok":
        await update.message.reply_text("Ссылка вредоносна\nСтатус ссылки:")
        await update.message.reply_text(json_response.get("url_status"))
        await update.message.reply_text("Хост:")
        await update.message.reply_text(json_response.get("host"))
        await update.message.reply_text("Угроза:")
        await update.message.reply_text(json_response.get("threat"))
        await update.message.reply_text(json_response.get("blacklists"))
        context.user_data["job"] = False
        return True

    elif json_response.get("query_status") == "no_results":
        await update.message.reply_text(
            "Ссылка не найдена среди вредоносных ( но это не значит, что ссылка абсолютно безопасна)"
        )
        context.user_data["job"] = False
        return False

    else:
        print(f"Unexpected response from URLhaus: {json_response}")
        await update.message.reply_text("Неверная ссылка. Попробуй ещё раз /check")
        context.user_data["job"] = False
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(" started")
    await update.message.reply_text(massage)

# Функция main():
def main():
    global API_KEY
    dotenv.load_dotenv()
    Token = os.getenv('TOKEN')
    API_KEY = os.getenv('API_KEY_TG')

    app = Application.builder().token(Token).build()

    app.bot_data["url_cache"] = TTLCache(maxsize=10000, ttl=24 * 60 * 60)
    app.add_handler(CommandHandler("check", check_url))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("advice", advice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, test))
    app.run_polling()


if __name__ == "__main__":
    main()
