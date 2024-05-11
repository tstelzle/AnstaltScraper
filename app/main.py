
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import calendar
from datetime import datetime
from telegram import Bot
import asyncio
import configparser
import schedule
import time

CONFIG = configparser.ConfigParser()
BASE_LINK = "https://lustspielhaus.de/events/{}/{}/all/"
CONFIG_FILE = "./config.ini"
YEAR_END = 2025
MONTH_END = 4


async def main():
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)

    result = {}

    for date in GetDates():
        value = IsAnstaltAvailableForMonth(driver, date)
        result[str.format("{}-{}", date[0], date[1])] = value

    driver.quit()

    result_string = '\n'.join([f"{key}: {value}" for key, value in result.items()])

    await send_message(result_string)
    

def IsAnstaltAvailableForMonth(currentdriver, date: tuple) -> str:
    year = date[0]
    month = date[1]
    num_days = calendar.monthrange(year, month)[1]
    start_day = f"{year}-{month:02d}-01"
    end_day = f"{year}-{month:02d}-{num_days}"

    monthLink = BASE_LINK.format(start_day, end_day)
    currentdriver.get(monthLink)

    events = currentdriver.find_elements(By.CLASS_NAME, "event-row")
    for event in events:
        artist_element = event.find_element(By.CLASS_NAME, "event-row-artist")

        if artist_element.text.strip() == 'DIE ANSTALT':
            # Find the 'event-row-notice' span to check if it contains 'Ausverkauft'
            notice_element = event.find_element(By.CLASS_NAME, 'event-row-notice')
            if notice_element.text.strip() == 'Ausverkauft':
                return "Ausverkauft"
            else:
                return "Verfügbar"
            
    return "Keine Show"


def GetDates():
    year_months = []

    current_year = datetime.now().year
    current_month = datetime.now().month

    while (current_year, current_month) <= (YEAR_END, MONTH_END):
        year_months.append((current_year, current_month))
        current_month += 1
        if current_month == 13:
            current_month = 1
            current_year += 1

    return year_months


async def send_message(message):
    bot = Bot(token=read_config_str("Telegram", "botToken"))
    try:
        response = await bot.send_message(chat_id=read_config_str("Telegram", "chatId"), text=message)
        print(response)
        return True
    except Exception as e:
        print(e)
        return False


def read_config_str(section: str, config_property: str) -> str:
    CONFIG.read(CONFIG_FILE)
    return CONFIG.get(section, config_property)


def run_main_async():
    asyncio.run(main())

schedule.every(30).minutes.do(run_main_async)

if __name__ == "__main__":
     while True:
        schedule.run_pending()
        time.sleep(28 * 60)