import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import pymongo
from taobaofood.config import *

driver = webdriver.Chrome()		#创建chrome浏览器对象
wait = WebDriverWait(driver,10)

conn = pymongo.MongoClient(MONGO_URL)
db = conn[MONGO_DB]

#解析首页
def search():
    try:
        driver.get("http://www.taobao.com")      #用浏览器打开url
        input = wait.until(EC.presence_of_element_located((By.ID, "q")))    #选择器选择页面搜索输入框
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#J_TSearchForm > div.search-button > button")))
        input.send_keys(KEYWORD)   #向浏览器传入搜索字符
        submit.click()	#模拟浏览器点击
        talpage = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#mainsrp-pager > div > div > div > div.total"))) 
        get_products_info()         #获取第一页商品信息
        return talpage.text		#返回页数总数
    except TimeoutException:
        return search()


#获取商品详情
def get_products_info():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist > div > div > div:nth-child(1)')))    #定位商品信息区块
    html = driver.page_source       #获取网页源代码
    doc = pq(html)       #pquery解析源码
    items = doc('#mainsrp-itemlist .items .item').items()       #获取商品信息div
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
        save_to_mongo(product)   #保存到MONGODB


#跳到下一页
def next_page(page_num):
    try:
        numinput = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input")))     #页码输入文本框
        numsubmit = wait.until( EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit")))       #页码点击确认框
        numinput.clear()     #清除页码输入框
        numinput.send_keys(page_num)    #输入页码
        numsubmit.click()       #点击确认
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,"#mainsrp-pager > div > div > div > ul > li.item.active > span"),str(page_num)))       #获取当前页码
        get_products_info()     #获取商品信息
    except TimeoutException:
        return next_page(page_num)

#存到数据库
def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):   #入库
            print("---保存到MONGODB成功---")
    except Exception:
        print("---保存到MONGODB失败---")


def main():
    try:
        total_page=search()
        total_page=int(re.compile("(\d+)").search(total_page).group(1))     #匹配总页数
        for i in range(2,total_page+1):
            print('-------第'+str(i)+'页--------')
            next_page(i)
    except Exception:
        print('---出错啦---')
    finally:
        driver.close()    #关闭浏览器


if __name__ == '__main__':
    main()
