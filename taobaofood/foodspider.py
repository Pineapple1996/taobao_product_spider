import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import pymongo
from taobaofood.config import *

driver = webdriver.Chrome()
wait = WebDriverWait(driver,10)

conn = pymongo.MongoClient(MONGO_URL)
db = conn[MONGO_DB]

def search():
    try:
        driver.get("http://www.taobao.com")
        input = wait.until(EC.presence_of_element_located((By.ID, "q")))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#J_TSearchForm > div.search-button > button")))
        input.send_keys(KEYWORD)
        submit.click()
        talpage = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#mainsrp-pager > div > div > div > div.total")))
        get_products_info()
        return talpage.text
    except TimeoutException:
        return search()

def get_products_info():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist > div > div > div:nth-child(1)')))
    html = driver.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for i in items:
        product={
            'pic':i.find('.pic .img').attr('src'),
            'price':i.find('.price').text(),
            'buymen':i.find('.deal-cnt').text()[:-3],
            'title':i.find('.J_ClickStat').text(),
            'shop':i.find('.shop').text(),
            'shoplink':i.find('.shopname').attr('href'),
            'location':i.find('.location').text()
        }
        save_to_mongo(product)

def next_page(page_num):
    try:
        numinput = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input")))
        numsubmit = wait.until( EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit")))
        numinput.clear()
        numinput.send_keys(page_num)
        numsubmit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,"#mainsrp-pager > div > div > div > ul > li.item.active > span"),str(page_num)))
        get_products_info()
    except TimeoutException:
        return next_page(page_num)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print("---保存到MONGODB成功---")
    except Exception:
        print("---保存到MONGODB失败---")

def main():
    try:
        total_page=search()
        total_page=int(re.compile("(\d+)").search(total_page).group(1))
        for i in range(2,total_page+1):
            print('-------第'+str(i)+'页--------')
            next_page(i)
    except Exception:
        print('---出错啦---')
    finally:
        driver.close()

if __name__ == '__main__':
    main()
