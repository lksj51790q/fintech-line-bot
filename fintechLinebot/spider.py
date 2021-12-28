# requests      用來對網站發出請求
# json          Python標準套件，用來處理JSON格式
# random        Python標準套件，用來隨機產生資料夾名稱
# os            Python標準套件，用來建立資料夾
# shutil        Python標準套件，用來快速刪除資料夾(一般刪除需要資料夾為空，此套件可以遞迴刪除)
# time          Python標準套件，用來計時刪除資料夾
import requests, json, random, os, shutil, time
# matplotlib    用來繪製圖表及表格
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.font_manager import FontProperties
# numpy         支援高階大量的維度陣列與矩陣運算，僅用來產生表格漸層顏色
import numpy as np
# pandas        可進行數據操作和分析，僅用來解析HTML內容
import pandas as pd
# bs4           BeautifulSoup用來解析HTML內容
from bs4 import BeautifulSoup

# 定義commodity_spider物件
class commodity_spider:
    def __init__(self, commodity): # 初始化
        self.commodity = commodity # 將傳入的原料參數作為成員變數
        self.url = 'http://www.stockq.org/commodity/js/' + self.commodity + '_sma.js' # 目標網址
        content = requests.get(self.url).text # 對目標網址發出請求並取出文本內容
        lines = content.split('\n') # 將每一行內容切分成list
        # 將想要的內容寫成JSON字串
        data_str = '['
        for line in lines:
            if line and line[0] == '[' and line[2] != '\'':
                data_str += line.replace('\'', '"')
        data_str += ']'

        self.data_list = json.loads(data_str) # 將JSON字串轉換成python物件
        self.x = [ele[0] for ele in self.data_list[1:]] # 日期資料
        self.y1 = [ele[1] for ele in self.data_list[1:]] # 價格資料
        self.y2 = [ele[2] for ele in self.data_list[1:]] # MA20資料
        self.y3 = [ele[3] for ele in self.data_list[1:]] # MA60資料
        rand_int = random.randint(0, 10000000) # 產生0~10000000的隨機整數
        while os.path.exists('./static/' + str(rand_int)): # 若隨機整數名稱的資料夾存在則重複
            rand_int = random.randint(0, 10000000) # 重新產生隨機整數
        self.path = '/static/' + str(rand_int) + '/' # 紀錄隨機整數名稱資料夾路徑
        os.mkdir('.' + self.path) # 建立資料夾
        return
    def __del__(self): # 物件被刪除時執行
        time.sleep(60) # 等60秒
        shutil.rmtree('.' + self.path) # 刪除隨機整數名稱資料夾及其內容
        return
    def draw_line_chart(self): # 將資料畫成折線圖儲存在隨機整數名稱資料夾
        fig = plt.figure(figsize=(20,15),dpi=300) # 設定圖片大小
        ax = fig.add_subplot(1, 1, 1) # 建立圖表
        plt.title(self.commodity, fontsize=28, fontweight='bold') # 設置標題
        ax.xaxis.set_major_locator(ticker.MultipleLocator(10)) # 設置x軸顯示名稱區間
        ax.yaxis.set_major_locator(ticker.MultipleLocator(50)) # 設置y軸顯示名稱區間
        plt.grid(True) # 畫出網格
        plt.plot(self.x, self.y1, color='r', linewidth=3) # 畫出價格線
        plt.plot(self.x, self.y2, color='#0000E3', ls='-', markeredgecolor='#343deb', linewidth=3) # 畫出MA20線
        plt.plot(self.x, self.y3, color='#D26900', ls='-', markeredgecolor='#343deb', linewidth=3) # 畫出MA60線
        plt.legend(('Price', 'MA20', 'MA60'), shadow=True, loc='best', handlelength=1.5, fontsize=20) # 畫出圖例
        plt.xlabel('Date ', fontsize=25, fontweight='bold', loc='right') # 設置x軸標題
        plt.ylabel('Price ', fontsize=25, fontweight='bold', loc='top') # 設置y軸標題
        plt.xticks(fontsize=15) # 設置x軸刻度標籤字體大小
        plt.yticks(fontsize=18) # 設置y軸刻度標籤字體大小
        plt.savefig('.' + self.path + 'plot.jpg', bbox_inches="tight", pad_inches=0.1, pil_kwargs={'quality':5}) # 儲存折線圖
        return self.path + 'plot.jpg' # 回傳路徑
    def draw_table(self): # 將最新十筆資料畫成表格儲存在隨機整數名稱資料夾
        collabel = self.data_list[0][1:] # 行標籤
        # 表格資料
        clust_data = [l[1:] for l in self.data_list[-10:]]
        clust_data = [["{:.1f}".format(ele) for ele in l] for l in clust_data]
        clust_data.reverse() # 將順序顛倒，變成最新的在前
        rowlabel = [l[0] for l in self.data_list[-10:]] # 列標籤
        rowlabel.reverse() # 將順序顛倒，變成最新的在前
        colcolours = ['#ff6666', '#788cff', '#ffa882'] # 設置行標籤顏色
        rowcolours = plt.cm.YlOrRd(np.linspace(0.4, 0, 10)) # 設置行標籤顏色為漸層顏色
        fig, ax = plt.subplots() # 建立圖表
        ax.axis('tight') # 設置圖表布局
        ax.axis('off') # 隱藏x，y軸
        ax.set_title(self.commodity, fontsize=15, fontweight='bold', verticalalignment='top', pad=80.0) # 設置標題
        # 畫表格
        the_table = ax.table(cellText=clust_data , colLabels=collabel, colColours=colcolours, loc='center', rowLabels=rowlabel, rowColours=rowcolours, cellLoc='center', fontsize=1000)
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(14)
        the_table.scale(1, 3)
        # 設置表格內容字體參數
        P = []
        for key, cell in the_table.get_celld().items():
            row, col = key
            P.append(cell)
        for x in P[30:]:
            x.set_text_props(fontproperties=FontProperties(weight='bold', size='large'))
        plt.savefig('.' + self.path + 'table.jpg', bbox_inches="tight", pad_inches=0.1, dpi=300, pil_kwargs={'quality':5}) # 儲存表格
        return self.path + 'table.jpg' # 回傳路徑

def get_newest_price_msg(commodity_name): # 抓原物料價格
    commodity_url = 'http://www.stockq.org/market/commodity.php' # 目標網址
    commodity = pd.read_html(commodity_url)[7] # 僅取出想要的內容
    commodity = commodity.drop(commodity.columns[0],axis=0) # 去除多餘部分
    commodity = commodity.drop(commodity.columns[1],axis=0) # 去除多餘部分
    commodity.columns = ['COMMODITY', 'PRICE', 'CHANGE', 'CHANGE_PERCENT', 'TIME'] # 設置行標籤
    commodity.set_index("COMMODITY", inplace = True) # 設置索引為"COMMODITY"行
    # 建構回傳訊息
    msg = commodity_name + '最新價格\n'
    msg += '買價：' + str(commodity.loc[commodity_name, "PRICE"]) + '\n'
    msg += '漲跌：' + str(commodity.loc[commodity_name, "CHANGE"]) + '\n'
    msg += '比例：' + str(commodity.loc[commodity_name, "CHANGE_PERCENT"])
    return msg # 回傳訊息

def get_newest_stock_price(stock_code): # 抓股票價格
    col_name = ['CODE', 'NAME', 'VOLUME', 'AMOUNT', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'PRICE_CHANGE', 'TRANSACTION'] # 定義行標籤
    col_ch_name = ["證券名稱","成交股數","成交金額","開盤價","最高價","最低價","收盤價","漲跌價差","成交筆數"] # 定義行中文標籤
    stock_url = 'http://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_dat' # 目標網址
    stock = pd.DataFrame(requests.get(stock_url).json()['data']) # 將網站想要的內容取出存成DataFrame物件
    stock.columns = col_name # 設置行標籤
    stock.set_index("CODE", inplace = True) # 設置索引為"CODE"行
    if not any(stock_code == stock.index): # 若股票代碼未在抓取的內容中出現
        return "找不到此公司股票。" # 回傳訊息
    # 建構回傳訊息
    msg = '證券代號：' + stock_code + '\n'
    for name, ch_name in zip(col_name[1:], col_ch_name):
        msg += ch_name + '：' + stock.loc[stock_code, name] + '\n'
    return msg.strip() # 回傳訊息

def get_stock_news(stock_id): # 抓股票新聞
    url = 'https://pchome.megatime.com.tw/stock/sid' + stock_id + '.html' # 目標網址
    # 設置請求標頭，防止被阻擋
    headers = {
        'referer': 'https://pchome.megatime.com.tw',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    }
    res = requests.get(url, headers=headers) # 發出請求
    soup = BeautifulSoup(res.text, 'lxml') # 解析網站回應
    if soup.find('div', id='stock_info_news') == None: # 檢查是否有此公司新聞
        return '查無此公司新聞。' # 回傳訊息
    # 建構回傳訊息
    response = ''
    for a in soup.find('div', id='stock_info_news').findAll('a')[:5]: # 僅加入前五筆新聞
        response += a.text + '\n' # 新聞標題
        response += 'https://pchome.megatime.com.tw' + a.get('href') + '\n' # 新聞超連結
    return response # 回傳訊息