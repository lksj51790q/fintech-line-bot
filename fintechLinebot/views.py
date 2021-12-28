# django    網頁框架
from django.shortcuts import render
from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# linebot   Linebot SDK，Line官方提供用來處理訊息的套件
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, FollowEvent
from linebot.models import TextSendMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction, CarouselTemplate, CarouselColumn
from linebot.models.messages import TextMessage, StickerMessage

# spider    自己寫的爬蟲套件，內容在spider.py
from .spider import commodity_spider, get_newest_price_msg, get_newest_stock_price, get_stock_news

# json      Python標準套件，用來處理JSON格式
import json

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN) # 建立LineBotApi物件，用來傳送回應
parser = WebhookParser(settings.LINE_CHANNEL_SECRET) # 建立WebhookParser物件，用來驗證及解析接收到的訊息
domain = settings.ALLOWED_HOSTS[-1] # 取得自己的網域名稱，定義在setting.py

commodity_dict = {
    "黃金": "COMMGOLD", 
    "銀": "COMMSILV", 
    "白金": "COMMPLAT", 
    "鈀": "COMMPALL", 
    "銠": "COMMRHDM", 
    "銅": "COMMCOPP", 
    "鎳": "COMMNIKL", 
    "鋁": "COMMALUM", 
    "鋅": "COMMZINC", 
    "鉛": "COMMLEAD", 
    "黃金期貨": "FUTRGOLD", 
    "銀期貨": "FUTRSILV", 
    "銅期貨": "FUTRCOPP", 
    "紐約輕原油": "FUTRWOIL", 
    "布蘭特油期": "FUTRBOIL", 
    "天然氣期": "FUTRNGAS", 
    "燃油期貨": "FUTRHOIL", 
    "無鉛汽油": "FUTRRBOB", 
    "玉米期貨": "FUTRCORN", 
    "小麥期貨": "FUTRWHEA", 
    "黃豆期貨": "FUTRBEAN", 
    "黃豆油期貨": "FUTRBNOL", 
    "活牛期貨": "FUTRCATT", 
    "瘦豬期貨": "FUTRHOGS", 
    "可可豆期": "FUTRCOCO", 
    "咖啡C期": "FUTRCOFF", 
    "十一號糖": "FUTRSUGR", 
    "二號棉期": "FUTRCTTN", 
    "XAU/USD": "XAUUSD", 
    "XAG/USD": "XAGUSD", 
    "倫敦銅期貨": "FUTRCOPPUK", 
    "倫敦鋁期貨": "FUTRALMNUK", 
    "倫敦鎳期貨": "FUTRNIKLUK", 
    "倫敦重柴油": "FUTRLNGO", 
    "碳排放期貨": "FUTRCRBN", 
    "倫敦咖啡豆": "FUTRLNCF"
}

industry_dict = {
    "1": "水泥工業",
    "2": "食品工業",
    "3": "塑膠工業",
    "4": "紡織工業",
    "5": "電機機械",
    "6": "電器電纜",
    "7": "化學生技業",
    "21": "化學工業",
    "22": "生技醫療",
    "8": "玻璃陶瓷",
    "9": "造紙工業",
    "10": "鋼鐵工業",
    "11": "橡膠工業",
    "12": "汽車工業",
    "13": "電子工業",
    "24": "半導體業",
    "25": "電腦及週邊設備業",
    "26": "光電業",
    "27": "通訊網路業",
    "28": "電子零組件業",
    "29": "電子通路業",
    "30": "資訊服務業",
    "31": "其他電子業",
    "14": "建材營造",
    "15": "航運",
    "16": "觀光",
    "17": "金融",
    "18": "貿易百貨",
    "23": "油電燃氣",
    "19": "綜合",
    "20": "其他",
    "80": "管理股票",
    "32": "文化創意業",
    "33": "農業科技",
    "34": "電子商務",
    "91": "台灣存託憑證",
    "97": "社會企業",
    "98": "農林漁牧",
    "-": "傳產其他"
}

with open('industry_news.json', encoding='UTF-8') as json_file:
    industry_news_dict = json.load(json_file)
with open('industry_analysis.json', encoding='UTF-8') as json_file:
    industry_analysis = json.load(json_file)
company_dict = {}
company_industry_dict = {}
with open("company.txt", 'r', encoding='UTF-8') as f:
    line = f.readline().strip()
    while line:
        com = line.split(',')
        company_dict[com[0]] = com[1]
        company_industry_dict[com[0]] = com[2]
        line = f.readline().strip()

@csrf_exempt # 使請求可以來自其他網域
def reply(request):
    if request.method == 'POST': # 若HTTP請求Method為POST
        # 解析請求內容
        signature = request.META['HTTP_X_LINE_SIGNATURE'] # 此request header用來驗證請求是由LINE Platform發出
        body = request.body.decode('utf-8') # 使用UTF-8編碼解碼請求內容
        try:
            events = parser.parse(body, signature) # 使用line sdk解析請求內容
        except InvalidSignatureError: # 若signature驗證失敗
            return HttpResponseForbidden() # 回傳http status code 403
        except LineBotApiError: # 若解析過程錯誤
            return HttpResponseBadRequest() # 回傳http status code 400
        # 處理事件
        for event in events:
            if isinstance(event, MessageEvent): # 若事件為訊息事件
                if isinstance(event.message, StickerMessage): # 若訊息內容為貼圖
                    # 傳送主功能選單
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='功能選單',
                            template=ButtonsTemplate(
                                title='產業資訊',
                                text='本功能提供查詢產業、原物料、特定公司等相關資訊。',
                                actions=[
                                    MessageTemplateAction(
                                        label='查詢特定公司相關資訊',
                                        text='特定公司相關資訊'
                                    ),
                                    MessageTemplateAction(
                                        label='查詢原物料價格',
                                        text='原物料價格'
                                    ),
                                    MessageTemplateAction(
                                        label='查詢產業相關資訊',
                                        text='產業相關資訊'
                                    )
                                ]
                            )
                        )
                    )
                elif not isinstance(event.message, TextMessage): # 若訊息內容為非文字及貼圖(邏輯上)
                    # 傳送文字訊息
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='請傳送文字或貼圖訊息。')
                    )
                elif event.message.text == "特定公司相關資訊": # 若接收到"特定公司相關資訊"文字訊息
                    # 傳送文字訊息
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="請輸入公司股票代碼\n例如：台泥請輸入「1101」")
                    )
                elif event.message.text == "產業相關資訊": # 若接收到"產業相關資訊"文字訊息
                    # 傳送產業輪播選單
                    button_list = []
                    count = 0
                    ### 將產業按鈕每三個分成一個sublist
                    for industry in industry_dict.values():
                        if count % 3 == 0:
                            button_list.append([]) # 插入新的空sublist
                        #在最後一個sublist放入按鈕
                        button_list[-1].append(
                            MessageTemplateAction(
                                label=industry,
                                text=industry
                            )
                        )
                        count += 1
                    ### 將選單分為兩則訊息
                    carousel_lists = [[], []]
                    for index, sub_button_list in enumerate(button_list[:7]):
                        carousel = CarouselColumn(
                                        title='產業' + str(index+1),
                                        text=' ',
                                        actions=sub_button_list
                                    )
                        carousel_lists[0].append(carousel)
                    for index, sub_button_list in enumerate(button_list[7:]):
                        carousel = CarouselColumn(
                                        title='產業' + str(index+8),
                                        text=' ',
                                        actions=sub_button_list
                                    )
                        carousel_lists[1].append(carousel)
                    ### 傳送訊息
                    line_bot_api.reply_message(
                        event.reply_token,
                        [
                            TemplateSendMessage(
                                alt_text='產業列表',
                                template=CarouselTemplate(
                                    columns=carousel_lists[0]
                                )
                            ),
                            TemplateSendMessage(
                                alt_text='產業列表',
                                template=CarouselTemplate(
                                    columns=carousel_lists[1]
                                )
                            )
                        ]
                    )
                elif event.message.text == "原物料價格": # 若接收到"原物料價格"文字訊息
                    # 傳送原物料輪播選單
                    button_list = []
                    count = 0
                    ### 將原物料按鈕每三個分成一個sublist
                    for commodity in commodity_dict.keys():
                        if count % 3 == 0:
                            button_list.append([]) # 插入新的空sublist
                        #在最後一個sublist放入按鈕
                        button_list[-1].append(
                            MessageTemplateAction(
                                label=commodity,
                                text=commodity
                            )
                        )
                        count += 1
                    ### 將選單分為兩則訊息
                    carousel_lists = [[], []]
                    for index, sub_button_list in enumerate(button_list[:6]):
                        carousel = CarouselColumn(
                                        title='原料' + str(index+1),
                                        text=' ',
                                        actions=sub_button_list
                                    )
                        carousel_lists[0].append(carousel)
                    for index, sub_button_list in enumerate(button_list[6:]):
                        carousel = CarouselColumn(
                                        title='原料' + str(index+7),
                                        text=' ',
                                        actions=sub_button_list
                                    )
                        carousel_lists[1].append(carousel)
                    ### 傳送訊息
                    line_bot_api.reply_message(
                        event.reply_token,
                        [
                            TemplateSendMessage(
                                alt_text='原物料列表',
                                template=CarouselTemplate(
                                    columns=carousel_lists[0]
                                )
                            ),
                            TemplateSendMessage(
                                alt_text='原物料列表',
                                template=CarouselTemplate(
                                    columns=carousel_lists[1]
                                )
                            )
                        ]
                    )
                elif '—' in event.message.text: # 若文字訊息中有破折號，正常應為按鈕回傳的指令
                    split_msg = event.message.text.split('—') # 將訊息以破折號切段
                    if split_msg[0] in commodity_dict.keys(): # 若第一段訊息為原物料名稱
                        if split_msg[1] == '價格走勢圖': # 若第二段訊息為"價格走勢圖"
                            spider = commodity_spider(commodity_dict[split_msg[0]]) # 宣告commodity_spider物件並傳入目標原物料名稱進行初始化
                            if spider: # 若commodity_spider物件初始化成功
                                line_chart_path = spider.draw_line_chart() # 繪製折線圖
                                table_path = spider.draw_table() # 繪製表格
                                # 傳送圖片
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    [ImageSendMessage(
                                        original_content_url='https://' + domain + line_chart_path, 
                                        preview_image_url='https://' + domain + line_chart_path
                                    ),
                                    ImageSendMessage(
                                        original_content_url='https://' + domain + table_path, 
                                        preview_image_url='https://' + domain + table_path
                                    )]
                                )
                        elif split_msg[1] == '最新價格': # 若第二段訊息為"最新價格"
                            # 傳送文字訊息，內容使用get_newest_price_msg(<原物料名稱>)及時抓取
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=get_newest_price_msg(split_msg[0]))
                            )
                    elif split_msg[0] in company_dict.keys(): # 若第一段訊息為公司股票代碼
                        if split_msg[1] == '股票價格': # 若第二段訊息為"股票價格"
                             # 傳送文字訊息，內容使用get_newest_stock_price(<公司股票代碼>)及時抓取
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=get_newest_stock_price(split_msg[0]))
                            )
                        elif split_msg[1] == '公司新聞': # 若第二段訊息為"公司新聞"
                            # 傳送文字訊息，內容使用get_stock_news(<公司股票代碼>)及時抓取
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=get_stock_news(split_msg[0]))
                            )
                    elif split_msg[0] in industry_dict.values(): # 若第一段訊息為產業名稱
                        if split_msg[1] == '產業分析': # 若第二段訊息為"產業分析"
                            # 傳送文字訊息，內容在industry_analysis.json中定義
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=industry_analysis[split_msg[0]])
                            )
                        elif split_msg[1] == '產業新聞': # 若第二段訊息為"產業新聞"
                            # 傳送文字訊息，內容在industry_news.json中定義
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=industry_news_dict[split_msg[0]])
                            )
                elif event.message.text in industry_dict.values(): # 若接收到產業名稱之文字訊息
                    # 傳送產業資訊功能選單
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text=event.message.text + '產業資訊',
                            template=ButtonsTemplate(
                                title=event.message.text,
                                text='請選擇欲查詢的項目。',
                                actions=[
                                    MessageTemplateAction(
                                        label='產業分析',
                                        text=event.message.text + '—產業分析'
                                    ),
                                    MessageTemplateAction(
                                        label='產業新聞',
                                        text=event.message.text + '—產業新聞'
                                    )
                                ]
                            )
                        )
                    )
                elif event.message.text in commodity_dict.keys(): # 若接收到原物料名稱之文字訊息
                    # 傳送原物料價格功能選單
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='原物料價格',
                            template=ButtonsTemplate(
                                title=event.message.text,
                                text='請選擇欲查詢的項目。',
                                actions=[
                                    MessageTemplateAction(
                                        label='價格走勢圖',
                                        text=event.message.text + '—價格走勢圖'
                                    ),
                                    MessageTemplateAction(
                                        label='最新價格',
                                        text=event.message.text + '—最新價格'
                                    )
                                ]
                            )
                        )
                    )
                elif event.message.text in company_dict.keys(): # 若接收到公司股票代碼之文字訊息
                    # 傳送該公司相關資訊功能選單
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='特定公司相關資訊',
                            template=ButtonsTemplate(
                                title=event.message.text + ' - ' + company_dict[event.message.text],
                                text='請選擇欲查詢的項目。',
                                actions=[
                                    MessageTemplateAction(
                                        label='股票價格',
                                        text=event.message.text + '—股票價格'
                                    ),
                                    MessageTemplateAction(
                                        label='公司新聞',
                                        text=event.message.text + '—公司新聞'
                                    ),
                                    MessageTemplateAction(
                                        label='產業相關資訊',
                                        text=industry_dict[company_industry_dict[event.message.text]]
                                    )
                                ]
                            )
                        )
                    )
                else: # 若接收到其他非相關文字訊息
                    # 傳送主功能選單
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='功能選單',
                            template=ButtonsTemplate(
                                title='產業資訊',
                                text='本功能提供查詢產業、原物料、特定公司等相關資訊。',
                                actions=[
                                    MessageTemplateAction(
                                        label='查詢特定公司相關資訊',
                                        text='特定公司相關資訊'
                                    ),
                                    MessageTemplateAction(
                                        label='查詢原物料價格',
                                        text='原物料價格'
                                    ),
                                    MessageTemplateAction(
                                        label='查詢產業相關資訊',
                                        text='產業相關資訊'
                                    )
                                ]
                            )
                        )
                    )
            elif isinstance(event, FollowEvent): # 若事件為追隨事件
                # 傳送主功能選單
                line_bot_api.reply_message(
                    event.reply_token,
                    TemplateSendMessage(
                        alt_text='功能選單',
                        template=ButtonsTemplate(
                            title='產業資訊',
                            text='本功能提供查詢產業、原物料、特定公司等相關資訊。',
                            actions=[
                                MessageTemplateAction(
                                    label='查詢特定公司相關資訊',
                                    text='特定公司相關資訊'
                                ),
                                MessageTemplateAction(
                                    label='查詢原物料價格',
                                    text='原物料價格'
                                ),
                                MessageTemplateAction(
                                    label='查詢產業相關資訊',
                                    text='產業相關資訊'
                                )
                            ]
                        )
                    )
                )
            # 未處理其他事件
        return HttpResponse() # 傳送空回應
    else: # 若HTTP請求Method為非POST
        return HttpResponse('HI!') # 在畫面上印出"HI!"，Debug用