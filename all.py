import pdfplumber
import pandas as pd
import numpy as np
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from pytz import timezone
import requests
from googletrans import Translator
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import gdown
import random

def get_weekday_index(weekday_name):
    """將中文星期轉為對應的數字索引 (0 = 星期一, ..., 6 = 星期日)"""
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    return weekdays.index(weekday_name)

def parse_date(description):
    today = datetime.today()
    weekday_today = today.weekday()  # 今天是星期幾 (0=Monday, ..., 6=Sunday)

    # 正則表達式匹配
    match = re.match(r"(上|這|下|下下)?禮拜([一二三四五六日])", description)
    if not match:
        raise ValueError("無法解析日期描述")

    modifier, target_weekday_name = match.groups()
    target_weekday = get_weekday_index(target_weekday_name)

    # 計算周數的偏移
    week_offset = {"上": -1, "這": 0, "下": 1, "下下": 2}.get(modifier, 0)

    # 計算目標日期
    days_until_target = (target_weekday - weekday_today) + (week_offset * 7)
    target_date = today + timedelta(days=days_until_target)

    return target_date.strftime("%Y-%m-%d")

def download_file(file_id, output_filename):
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output_filename, quiet=False)
        print(f"檔案已下載並儲存為: {output_filename}")
    except Exception as e:
        print(f"下載檔案失敗: {output_filename}, 錯誤: {e}")

def delet_data_of_school(user_id):
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    worksheet.batch_clear(['D1:D50'])
    worksheet.batch_clear(['E1:E50'])
    worksheet.batch_clear(['F1', 'G1'])
  
def basic_information(user_id,data):
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    index_data = list(data.split())
    basic_data = [['起床時間:'+index_data[0]], ['睡覺時間:'+index_data[1]], ['早餐所需時間:'+index_data[2]+'分鐘'], ['午餐所需時間:'+index_data[3]+'分鐘'], ['晚餐所需時間:'+index_data[4]+'分鐘'], ['早上梳洗所需時間:'+index_data[5]+'分鐘'], ['晚上沐浴所需時間:'+index_data[6]+'分鐘']]
    worksheet.update(basic_data, "A1")


#課表(中文版一頁)
def curriculum(user_id,drive_url) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    match = re.search(r'/d/([a-zA-Z0-9_-]+)/', drive_url)
    if not match:
        print("無效的 Google Drive 連結！")
        return -1
    file_id = match.group(1)
    file_output_name = user_id+'_e.pdf'
    download_file(file_id, file_output_name)
      
    with pdfplumber.open(file_output_name) as pdf:
        total_pages = len(pdf.pages)  # 獲取總頁數
        all_tables = []
        for page_num in range(total_pages):  # 遍歷每一頁提取表格
            page = pdf.pages[page_num]
            table = page.extract_table()
            table.pop()
            t = []
            for i in range(1,len(table)-1,2):
                for j in range(1,7):
                    table[i+1][j] = table[i][j]
            rows_to_delete = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29]
            table = np.delete(table, rows_to_delete, axis=0)
            df = pd.DataFrame(table[1:], columns=table[0])
            all_tables.append(df)
    final = []
    for i in range(1,7):
        for j in range(1,16):
            if  table[j][i].replace("\n"," ") != '' :
                final.append([table[0][i]+table[j][0]+' '+table[j][i].replace("\n"," ")])
    worksheet.update(final, "D1")

#行事曆(學校中文版)
def calendar(user_id,drive_url,keyword) :
    keywords = keyword.split()
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    match = re.search(r'/d/([a-zA-Z0-9_-]+)/', drive_url)
    if not match:
        print("無效的 Google Drive 連結！")
        return -1
    file_id = match.group(1)
    file_output_name = user_id+'_c.pdf'
    download_file(file_id, file_output_name)
  
    with pdfplumber.open(file_output_name) as pdf:
        total_pages = len(pdf.pages)  # 獲取總頁數
        all_tables = []
        k = 0
        for page_num in range(total_pages):  # 遍歷每一頁提取表格
            page = pdf.pages[page_num]
            table_settings = {
            "vertical_strategy": "lines",  # 或 "text"
            "horizontal_strategy": "lines"  # 或 "text"
            }
            table = page.extract_table(table_settings)
            rows_to_delete = [1, 2, 3, 4, 5, 6, 7, 8]
            for i in range(1, len(table)):
                # 確保 table[i][1] 不為 None
                if table[i][1] is None:
                    continue
                table[i] = np.delete(table[i], rows_to_delete)
                if k == 0:
                    all_tables.append(np.array([table[0][0], table[0][1]]))
                    all_tables.append([])
                    k = 1
                formatted_data = []# 提取日期和事項
                header = table[i][0]  # 假設第一個元素是標題部分
                events = table[i][1].split('\n')  # 按換行符分割事件
                for event in events:  # 將每個事件與標題配對
                    formatted_data.append([header, event])  # 創建新的 numpy array 並添加到列表
                all_tables[1].extend(formatted_data)
    length = len(all_tables[1])
    date_pattern = r'\(\d\)'  # 匹配像 (1) 這樣的格式
    for i in range(length):
        all_tables[1][i][1] = re.sub(date_pattern, '', all_tables[1][i][1])  # 刪除 (1) (2) (3) (4) (5) (6)
        all_tables[1][i][1] = ' '.join(all_tables[1][i][1].split())  # 去除多餘的空格
    previous_year = None
    for i in range(1, length):
        if all_tables[1][i][0]:  # 如果 header 不為空
            header = all_tables[1][i][0]
            year_match = re.match(r"(\d+年)", header)  # 提取年份
            if year_match: previous_year = year_match.group(1)
            else: header = previous_year + " " +header  # 如果沒有年份，就沿用上一行的年份
            all_tables[1][i][0] = header
    date_pattern = r'(\d{1,2}/\d{1,2}-\d{1,2}/\d{1,2}|\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2}日|\d{1,2}日)' # 改進正則表達式，正確匹配日期範圍
    for i in range(length):
        year_month = all_tables[1][i][0].replace('\n', ' ')  # 去除第一個欄位中的換行符號
        all_tables[1][i][0] = year_month
        split_item = re.split(date_pattern, all_tables[1][i][1]) # 分割第二個欄位中的日期和描述
        clean_elements = [elem.strip() for elem in split_item if elem.strip()] # 將分割後的內容清理並組合
        combined_result = [year_month]  # 初始化合併結果，並保留年和月
        if clean_elements:
            combined_result.append(clean_elements[0])  # 加入描述部分
        k = 0
        for j in range(1, len(clean_elements)):
            if re.match(date_pattern, clean_elements[j]):
                continue
            if '（放假' in clean_elements[j] and combined_result[-1].endswith("（放假") or k>=1 :
                combined_result[-1] += clean_elements[j]  # 合併當前元素
            else:
                combined_result.append(clean_elements[j])  # 否則，直接加入當前元素
                k = k + 1
        all_tables[1][i] = combined_result
    all_tables[0] = ['月份/日期 : 工作事項']
    all_tables_row = []
    if all_tables:
        for i in range(len(all_tables[1])):
            for k in keywords:
                if k in all_tables[1][i][2] :
                    all_tables_row.append([f'{all_tables[1][i][0]}/{all_tables[1][i][1]} : {all_tables[1][i][2]}'])
    worksheet.update(all_tables_row, "E1")

# list提醒
def daily_remind_list(user_id) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    remind = ''
    worksheet = sh.worksheet(user_id)
    column_a_values = worksheet.col_values(3)
    for i in range(len(column_a_values)):
        remind = remind + f'{i+1}. {column_a_values[i]}\n'
    return remind

# add提醒
def daily_remind_add(user_id,remind) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    column_a_values = []
    row_value = remind.split('\n')
    for i in range(len(row_value)):
        parts = row_value[i].split()  # 預設分隔符為任意數量空格
        column_a_values.append(parts[0]+' '+parts[1])
    #   formatted_values = [[value] for value in column_a_values]
    for value in column_a_values :
        last_row = len(worksheet.col_values(3)) + 1
        worksheet.update_cell(last_row, 3, value)  # (行號, 列號, 要添加的值)
    #   worksheet.update(formatted_values, "C1")
  
#delet提醒
def daily_remind_delet(user_id,number_duty) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    column_a_values = worksheet.col_values(3)
    index_remind = list(map(int, number_duty.split()))
    for i in range(len(index_remind) - 1, -1, -1):
        del column_a_values[index_remind[i]-1]
    worksheet.batch_clear(['C1:C50'])
    formatted_values = [[value] for value in column_a_values]
    worksheet.update(formatted_values, "C1")
  
# list任務
def daily_tasks_list(user_id) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    duty = ''
    worksheet = sh.worksheet(user_id)
    column_a_values = worksheet.col_values(2)
    for i in range(len(column_a_values)):
        duty = duty + f'{i+1}. {column_a_values[i]}\n'
    return duty

# add任務
def daily_tasks_add(user_id,duty) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    column_a_values = []
    row_value = duty.split('\n')
    for i in range(len(row_value)):
        parts = row_value[i].split()
        temp = parse_date(parts[2])
        column_a_values.append(parts[0]+' '+parts[1]+' '+temp+"前完成")
    for value in column_a_values :
        last_row = len(worksheet.col_values(2)) + 1
        worksheet.update_cell(last_row, 2, value)  # (行號, 列號, 要添加的值)
    #   worksheet.update(formatted_values, "B1")
  
# delet任務
def daily_tasks_delet(user_id, number_duty) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    column_a_values = worksheet.col_values(2)
    index_duty = list(map(int, number_duty.split()))
    for i in range(len(index_duty) - 1, -1, -1):
        del column_a_values[index_duty[i]-1]
    worksheet.batch_clear(['B1:B50'])
    formatted_values = [[value] for value in column_a_values]
    worksheet.update(formatted_values, "B1")
  
def daily_tasks_delet_masch(user_id, tast_sch) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    column_a_values = worksheet.col_values(2)
    tast_sch_part = tast_sch.split('\n')
    filtered_parts = [
        part for part in column_a_values
        if not any(part.split()[0] == part_sch.split()[0] for part_sch in tast_sch_part)
        ]
    worksheet.batch_clear(['E1:E50'])
    worksheet.update(filtered_parts, "B1")
  
# 加任務 for google calendar
def add_task(user_id, summary, start_time, end_time) :
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    J1_value = worksheet.acell('J1').value
    J2_value = worksheet.acell('J2').value
    json_file = J1_value
    calendar_id = J2_value
    credentials = service_account.Credentials.from_service_account_file(
        json_file, scopes=['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=credentials)
    event = { # Create a new event
        'summary': summary,
        'start': {
            'dateTime': start_time ,
            # current_time.isoformat(),
            'timeZone': 'Asia/Taipei',
        },
        'end': {
            'dateTime': end_time ,
            #  (current_time + timedelta(hours=1)).isoformat(),
            'timeZone': 'Asia/Taipei',
        },
    }
    event = service.events().insert(calendarId=calendar_id, body=event).execute()  # Insert the event into the calendar
  
# 找時間
def get_time_period(start_time_obj):
    from datetime import datetime, timedelta
    current_time = datetime.now()
    if start_time_obj.date() == current_time.date():
        day_str = "今天"
    elif start_time_obj.date() == (current_time.date() + timedelta(days=1)):
        day_str = "明天"
    elif start_time_obj.date() == (current_time.date() + timedelta(days=2)):
        day_str = "後天"
    else:
        day_str = start_time_obj.strftime('%Y-%m-%d')  # 超過三天，顯示具體日期
        hour = start_time_obj.hour
    if 6 <= hour < 12:
        period_str = "早上"
    elif 12 <= hour < 17:
        period_str = "下午"
    else:
        period_str = "晚上"
    return f"{day_str} {period_str}"

# # 找台北市天氣
# def check_Taipei(user_id,keyword) :
#     keyword = keyword.replace('台北市','')
#     keyword = keyword.replace('臺北市','')
#     SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
#     SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
#     credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#     gc = gspread.authorize(credentials)
#     SHEET_NAME = "linebot_assisant"
#     sh = gc.open(SHEET_NAME)
#     worksheet = sh.worksheet(user_id)
#     column_a_values = worksheet.col_values(8)
#     from datetime import datetime, timedelta
#     url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-061?Authorization=CWA-4024E8A2-DA54-41EA-A04B-38AFE6CE41D8'
#     data = requests.get(url)   # 取得 JSON 檔案的內容為文字
#     data_json = data.json()    # 轉換成 JSON 格式
#     location_all = data_json['records']['locations']
#     for i in location_all:
#         city_name = i['locationsName']
#         for j in range(12):
#             area = i['location'][j]['locationName']
#             if area not in keyword :
#                 continue
#             for k in range(11):
#                 if k==1 :
#                     description = i['location'][j]['weatherElement'][k]['description']
#                     for q in range(6):
#                         start_time = i['location'][j]['weatherElement'][k]['time'][q]['startTime']
#                         # end_time = i['location'][j]['weatherElement'][k]['time'][q]['endTime']
#                         value_number = i['location'][j]['weatherElement'][k]['time'][q]['elementValue'][0]['value']
#                         # print(f'時間:{start_time}~{end_time}  :  {value_number}')
#                         start_time_obj = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
#                         start_time_str = get_time_period(start_time_obj)
#                         column_a_values.append(f'{city_name+area} {description} {start_time_str} {value_number}')
#     formatted_values = [[value] for value in column_a_values]
#     worksheet.update(formatted_values, "H1")

# # 找新北市天氣
# def check_Newtaipei(user_id,keyword) :
#     keyword = keyword.replace('新北市','')
#     SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
#     SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
#     credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#     gc = gspread.authorize(credentials)
#     SHEET_NAME = "linebot_assisant"
#     sh = gc.open(SHEET_NAME)
#     worksheet = sh.worksheet(user_id)
#     column_a_values = worksheet.col_values(8)
#     from datetime import datetime, timedelta
#     url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-069?Authorization=CWA-4024E8A2-DA54-41EA-A04B-38AFE6CE41D8'
#     data = requests.get(url)   # 取得 JSON 檔案的內容為文字
#     data_json = data.json()    # 轉換成 JSON 格式
#     location_all = data_json['records']['locations']
#     for i in location_all:
#         city_name = i['locationsName']
#         for j in range(29):
#             area = i['location'][j]['locationName']
#             if area not in keyword :
#                 continue
#             for k in range(11):
#                 if k==1 :
#                     description = i['location'][j]['weatherElement'][k]['description']
#                     for q in range(6):
#                         start_time = i['location'][j]['weatherElement'][k]['time'][q]['startTime']
#                         end_time = i['location'][j]['weatherElement'][k]['time'][q]['endTime']
#                         value_number = i['location'][j]['weatherElement'][k]['time'][q]['elementValue'][0]['value']
#                         start_time_obj = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
#                         start_time_str = get_time_period(start_time_obj)
#                         column_a_values.append(f'{city_name+area} {description} {start_time_str} {value_number}')
#     formatted_values = [[value] for value in column_a_values]
#     worksheet.update(formatted_values, "H1")

def location_weather(user_id,city_loca):
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    worksheet.update([[city_loca]], "G1")
    # row_value = city_loca.split()
    # for i in range(len(row_value)):
    #     if '新北市' in row_value[i]: 
    #         check_Newtaipei(user_id,row_value[i])
    #     elif '台北市' in row_value[i] or '臺北市' in row_value[i]: 
    #         check_Taipei(user_id,row_value[i])
  
def save_communication_time(user_id,time_com):
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    worksheet.update([[time_com + '分鐘']], "F1")
  
def save_json(user_id,drive_url):
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    # 從 Google Drive 連結中提取檔案 ID
    match = re.search(r'/d/([a-zA-Z0-9_-]+)/', drive_url)
    if not match:
        print("無效的 Google Drive 連結！")
        return -1
    file_id = match.group(1)
    file_output_name = user_id+'.json'
    download_file(file_id, file_output_name)
    worksheet.update([[file_output_name]], "J1")

def save_ID(user_id,user_message):
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(user_id)
    worksheet.update([[user_message]], "J2")

def send_water(u_id,date):
    import random
    text_rd = random.choice(['補充水分', '記得喝水', '你喝水了嗎', '你是不是忘記什麼了  是喝水喔~', '水 水水 水水水', '水啊~', '休息一下 ，喝個水!', '喝~水~'])

    add_task(u_id, text_rd, date[0]+'T10:00:00', date[0]+'T10:00:00')
    add_task(u_id, text_rd, date[0]+'T11:10:00', date[0]+'T11:10:00')
    add_task(u_id, text_rd, date[0]+'T14:10:00', date[0]+'T14:10:00')
    add_task(u_id, text_rd, date[0]+'T15:10:00', date[0]+'T15:10:00')
    add_task(u_id, text_rd, date[0]+'T18:00:00', date[0]+'T18:00:00')

def send_AM_PM(u_id,date):
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    string_remain = ''
    string_remain_2 = ''
    string_remain_3 = ''
    flag_weather = 0
    worksheet = sh.worksheet(u_id)
    remind_part = worksheet.col_values(3)
    weather_part = worksheet.col_values(8)
    for wea in weather_part :
        if '雨' in wea : flag_weather=1
    if flag_weather : 
        # 2024-10-25T07:30:00
        string_remain = '要記得帶雨傘喔!'
    for parts in remind_part :
        if '早上' in parts :
            part = parts.split()
            string_remain = string_remain + part[0] + '\n'
        elif '中午' in parts :
            part = parts.split()
            string_remain_2 = string_remain_2 + part[0] + '\n'
        elif '晚上' in parts :
            part = parts.split()
            string_remain_3 = string_remain_3 + part[0] + '\n'
    if string_remain :
        add_task(u_id, string_remain, date[0]+'T07:30:00', date[0]+'T07:30:00')
    if string_remain_2 :
        add_task(u_id, string_remain_2, date[0]+'T12:10:00', date[0]+'T12:10:00')
    if string_remain_3 :
        add_task(u_id, string_remain_3, date[0]+'T18:30:00', date[0]+'T18:30:00')

def make_sch(u_id):
    schedule_text = """
    2024-10-25 星期五 行程規劃

    早上:
    07:00: 起床，準備出門。
    07:30 - 08:30:  出發前往學校。
    08:40 - 09:10:  預習「控制系統」課程內容。
    09:10 - 12:10:  「控制系統」課程，地點：工 401。

    下午:
    12:10 - 13:10:  午餐時間。
    13:20 - 15:10:  「電機專題製作（一）」課程，地點：電機系電子實驗室。
    15:10 - 17:10:  完成「專題  兩個小時  2024-11-6前完成」。
    17:10 - 18:10:  出發回家

    晚上:
    18:10 - 18:30:  晚餐時間。
    18:30 - 21:00:  完成「類比作業 兩個半小時  2024-11-6前完成」。
    21:00 - 22:00:  自由活動，可選擇看書或追劇。
    22:00:  洗漱，準備睡覺。

    任務完成：
    專題  兩個小時  2024-11-6前完成
    類比作業 兩個半小時  2024-11-6前完成
    """
    SERVICE_ACCOUNT_FILE = "static-destiny-436012-i9-ab054a535fd6.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    SHEET_NAME = "linebot_assisant"
    sh = gc.open(SHEET_NAME)
    
    import google.generativeai as genai
    apikey = 'API'
    genai.configure(api_key=apikey)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    import datetime
    today = datetime.date.today()
    weekday = today.weekday()
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    first_date = "今天:"+str(today)+days[weekday]
    print('======================================================================')
    wt = sh.worksheet(u_id)
    wt.batch_clear(['H1:H50'])
    g1_value = wt.acell('G1').value
    # row_value = g1_value.split()
    # for i in range(len(row_value)):
    #     if '新北市' in row_value[i]: 
    #         check_Newtaipei(u_id,row_value[i])
    #     elif '台北市' in row_value[i] or '臺北市' in row_value[i]: 
    #         check_Taipei(u_id,row_value[i])
    response = model.generate_content(
        "可以請你做一份明天一天的規劃嗎(不需要備註)"
        + "  計畫範例:" + schedule_text
        + str(first_date)
        + "  基礎:" + str(wt.col_values(1))
        + "  課表:" + str(wt.col_values(4))
        + "  特殊假日:" + str(wt.col_values(5))
        + "  任務:" + str(wt.col_values(2))
        + "  交通時間:" + str(wt.col_values(6))
        + "  地點天氣:" + str(wt.col_values(8))
        )
    print('======================================================================')
    # print(response.text)
    # sections = response.text.split("任務完成：")
    # schedule = sections[0].strip()  # 行程規劃部分
    # tasks = sections[1].strip()  # 任務完成部分
    # schedule = schedule+'\n祝你一切順利!'
    # daily_tasks_delet_masch(u_id,tasks)
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", response.text)
    date = [date_match.group()] if date_match else []
    # lines = re.findall(r"(\d{2}:\d{2}(?: - \d{2}:\d{2})?):\s*(.+)", schedule)
    # time_intervals = [line[0] for line in lines]
    #   descriptions = [line[1].strip() for line in lines]
    J2_value = wt.acell('G1').value
    print(date)
    print('======================================================================')
    if J2_value :
        send_AM_PM(u_id,date)
        send_water(u_id,date)
        # for j in range(len(time_intervals)):
        # # 2024-10-25T07:30:00
        #     if part := time_intervals[j].split(' - ') : add_task(u_id, lines[1][j], date+'T'+part[0]+':00', date+'T'+part[1]+':00')
        #     else : add_task(u_id, lines[1][j], date+'T'+time_intervals[j]+':00', date+'T'+time_intervals[j]+':00')
    return response.text

import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, TemplateSendMessage
from linebot.models import StickerSendMessage, ButtonsTemplate, URIAction
from pyngrok import ngrok


app = Flask(__name__)

line_bot_api = LineBotApi('q3D+yarl7RWbNx9w5GccNE405MY3PQLeW9mL52roBDupSK0Q7ZWUdly21XU2PsdTOXrEXf7GnPHyGyz5bIzsM4R7zbvvuG8GOyz69FUedB/Wyn2X+EtsMe4K9SUnU/Nf9Eoz3vfDxzXZZrXaimUWLAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('dc77d38f2b719db16ccff3434f674945')
global opinion_flag 
global check_number 
global keyword_c 
global flag_google
opinion_flag = [0 for i in range(13)]
check_number = -1
keyword_c = '放假'
flag_google = [0 for i in range(2)]

# 設置 Webhook 處理函數
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 設置當用戶加入時的事件
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_file(
        'static-destiny-436012-i9-ab054a535fd6.json',
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open("linebot_assisant")
    new_sheet_name = f'{user_id}'  # 設定新工作表名稱
    rows = 100  # 設定行數
    cols = 20   # 設定列數
    new_worksheet = spreadsheet.add_worksheet(title=new_sheet_name, rows=rows, cols=cols)
    worksheet = spreadsheet.worksheet(new_sheet_name)
    worksheet = spreadsheet.worksheet('main')
    last_row = len(worksheet.col_values(1)) + 1
    worksheet.update_cell(last_row, 1, user_id)  # (行號, 列號, 要添加的值)
    welcome_message = TextSendMessage(text="歡迎加入\n我是你的生活小助手\n一開始填的資料比較多 請加油")
    welcome_message_1 = TextSendMessage(text="可以輸入'嗨'可以看目錄\n生成計畫請晚上\n因為不支援pdf，所以有關的動作會有意點麻煩")
    # 傳送貼圖訊息，選擇一個 sticker_id 和 package_id
    welcome_sticker = StickerSendMessage(
        package_id='11537',  # 貼圖包 ID
        sticker_id='52002738'   # 貼圖 ID
    )

    # 回覆文字訊息和貼圖
    line_bot_api.reply_message(
        event.reply_token,
        [welcome_message, welcome_message_1, welcome_sticker]
    )

# 設置接收訊息的事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    quick_buttons = ["嗯", "添加任務", "添加提醒", "刪除任務", "刪除提醒", "學期結束", "輸入基本資料", "輸入天氣地區", "上傳課表", "上傳行事曆", "同步google calender","計畫明天"]
    if user_message=='嗨' :
        print('222222222')
        m_text = ''
        for i in range(len(quick_buttons)):
            m_text = m_text + quick_buttons[i] + '\n'
            message = TextSendMessage(text=m_text)
    else :
        print('222')
        check_number=-1
        for i in range(13):
            if opinion_flag[i]==1 : check_number=i
        print(check_number)
        if user_message=='嗯':
            print('2216156')
            package_id = random.choice(['11537', '11538', '11539'])
            if package_id=='11537' :  sticker_id = random.choice([str(i) for i in range(52002734, 52002774)])
            elif package_id=='11538' : sticker_id = random.choice([str(i) for i in range(51626494, 51626533)])
            elif package_id=='11539' : sticker_id = random.choice([str(i) for i in range(52114110, 52114149)])
            message = StickerSendMessage(package_id=package_id, sticker_id=sticker_id)
        elif check_number == -1 :
            print("未找到啟用的 opinion_flag，請檢查邏輯。")
            if user_message == '添加任務':
                message_1 = TextSendMessage(text="輸入格式:\n任務名稱 時間 期限(這禮拜一or下下禮拜二)\n例如:\n作業 1小時 這禮拜一\n看書 半小時 下下禮拜五\n\n可以輸入多行")
                message_2 = StickerSendMessage(
                package_id='11538',  # 貼圖包 ID
                sticker_id='51626518'   # 貼圖 ID
                )
                message_3 = TextSendMessage(text='現有任務:\n'+daily_tasks_list(user_id))
                message = [ message_1, message_2, message_3 ]
                opinion_flag[1]=1
            elif user_message == '添加提醒':
                message_1 = TextSendMessage(text="輸入格式:\n提醒名稱\n頻率(每天)(可以輸入早上or中午or晚上)\n例如:吃藥 早上晚上\n\n可以輸入多行")
                message_2 = StickerSendMessage(
                package_id='11538',  # 貼圖包 ID
                sticker_id='51626518'   # 貼圖 ID
                )
                message_3 = TextSendMessage(text='現有提醒:\n'+daily_remind_list(user_id))
                message = [ message_1, message_2, message_3 ]
                opinion_flag[2]=1
            elif user_message == '刪除任務':
                message_2 = TextSendMessage(text='請輸入要刪除的任務\n例如:1 5 6')
                message_3 = TextSendMessage(text='現有任務:\n'+daily_tasks_list(user_id))
                message = [ message_2, message_3 ]
                opinion_flag[3]=1
            elif user_message == '刪除提醒':
                message_2 = TextSendMessage(text='請輸入要刪除的提醒\n例如:1 5 6')
                message_3 = TextSendMessage(text='現有提醒:\n'+daily_remind_list(user_id))
                message = [ message_2, message_3 ]
                opinion_flag[4]=1
            elif user_message == '學期結束':
                delet_data_of_school(user_id)
                message_1 = StickerSendMessage(
                package_id='11537',  # 貼圖包 ID
                sticker_id='52002763'   # 貼圖 ID
                )
                message_2 = TextSendMessage(text='請重新輸入輸入天氣地區\nPS.只要輸入OO市OO區')
                message = [message_1, message_2]
                opinion_flag[7]=1
            elif user_message == '輸入基本資料':
                print('1111111')
                message = TextSendMessage(text="請你輸入:\n幾點起床 幾點睡覺 早餐所需時間 午餐所需時間 晚餐所需時間 早上梳洗所需時間 晚上沐浴所需時間 (單位:分鐘)\n例如: 7:00 23:30 30 60 60 30 60")
                opinion_flag[6]=1
            elif user_message == '輸入天氣地區':
                message = TextSendMessage(text=f"你可以輸入一個或兩個(只支援新北市台北市)\n例如:新北市三重區，\n新北市三重區 台北市信義區")
                opinion_flag[7]=1
            elif user_message == '上傳課表':
                message = TextSendMessage(text="等一下請先把學校課表的pdf(中文版)傳到雲端\n之後再把共享設置成知道連結者都可使用\n傳分享網址給我")
                opinion_flag[8]=1
            elif user_message == '上傳行事曆':
                message = TextSendMessage(text="等一下請先把學校行事曆的pdf(中文版)傳到雲端\n之後再把共享設置成知道連結者都可使用\n傳分享網址給我")
                opinion_flag[9]=1
            elif user_message == '同步google calender':
                message_1 = TextSendMessage(text="等一下請先把json傳到雲端\n之後再把共享設置成知道連結者都可使用\n傳分享網址給我之後再輸入calendarId")
                message_2 = TemplateSendMessage(
                alt_text='參考link',
                template=ButtonsTemplate(
                    text='點擊',
                    actions=[
                    URIAction(label='網站', uri='https://medium.com/@anthea.ensui/web-net-google-calendar-api-5dc75fd1a6ce')
                    ]
                )
                )
                message_3 = TextSendMessage(text="等一下請上傳json")
                message = [ message_1, message_2, message_3 ]
                opinion_flag[10]=1
            elif user_message=='計畫明天':
                message_1 = TextSendMessage(text="計畫的任務請手動刪除")
                message_2 = TextSendMessage(text=make_sch(user_id))
                message = [ message_1, message_2]
        elif check_number == 1 :
            daily_tasks_add(user_id,user_message)
            message_1 = TextSendMessage(text="成功")
            message_2 = TextSendMessage(text='現有任務:\n'+daily_tasks_list(user_id))
            message = [message_1, message_2]
            opinion_flag[1]=0
        elif check_number == 2 :
            daily_remind_add(user_id,user_message)
            message_1 = TextSendMessage(text="成功")
            message_2 = TextSendMessage(text='現有提醒:\n'+daily_remind_list(user_id))
            message = [message_1, message_2]
            opinion_flag[2]=0
        elif check_number == 3 :
            daily_tasks_delet(user_id,user_message)
            message_1 = TextSendMessage(text="成功")
            message_2 = TextSendMessage(text='現有任務:\n'+daily_tasks_list(user_id))
            message = [message_1, message_2]
            opinion_flag[3]=0
        elif check_number == 4 :
            daily_remind_delet(user_id,user_message)
            message_1 = TextSendMessage(text="成功")
            message_2 = TextSendMessage(text='現有提醒:\n'+daily_remind_list(user_id))
            message = [message_1, message_2]
            opinion_flag[4]=0
        elif check_number == 6 :
            basic_information(user_id,user_message)
            message = TextSendMessage(text="填寫完成")
            opinion_flag[6]=0
        elif check_number == 7 :
            user_me = user_message.isdigit()
            if user_me :
                save_communication_time(user_id,user_message)
                message = TextSendMessage(text="交通時間填寫完成")
                opinion_flag[7]=0
            else :
                user_me = user_message.split()
                if len(user_me)==1 :
                    location_weather(user_id,user_message)
                    message = TextSendMessage(text="地區填寫完成")
                    opinion_flag[7]=0
                elif len(user_me)==2 :
                    location_weather(user_id,user_message)
                    message_1 = TextSendMessage(text='地區填寫完成')
                    message_2 = TextSendMessage(text="請輸入交通時間長度(不要太趕的)\nPS.單位:分鐘")
                    message = [message_1, message_2]
        elif check_number == 8 :
            curriculum(user_id,user_message)
            message = TextSendMessage(text="完成")
            opinion_flag[8]=0
        elif check_number == 9 :
            calendar(user_id,user_message,keyword_c)
            message = TextSendMessage(text="完成")
            opinion_flag[9]=0
        elif check_number == 10 :
            if flag_google[0]==0: #J
                save_json(user_id,user_message)
                message_1 = TextSendMessage(text="已收到您的 json 檔案！")
                message_2 = TextSendMessage(text="請輸入calendarId")
                message = [message_1, message_2]
                flag_google[0] = 1
            else :
                save_ID(user_id,user_message)
                message = TextSendMessage(text="完成")
                flag_google[0] = 0
                opinion_flag[10]=0

    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run(port=5000)

# user_id = 'U581f8a3b61b495520a7640d94f7fac29'
# user_message_basis = '7:00 23:30 30 60 60 30 60'
# user_message_remind_ini = '喝水 早上中午晚上\n抹藥 早上晚上\n點藥水 早上晚上'
# user_message_task_ini = '類比作業 3小時 這禮拜三\n畫畫 半小時 下禮拜三\n物件導向 3小時 這禮拜五\n機器學習 下下禮拜五'
# user_message_remind = '吃藥 中午\n雨傘 早上'
# user_message_task = '演算法 3小時 下禮拜四\n看書 2小時 這禮拜六'
# user_message_remind_index = '3 4'
# user_message_task_index = '2 6'
# user_message_e = 'https://drive.google.com/file/d/1p0SPdlfAeCGsrN_BpUUGO19aV9vj-e1E/view?usp=sharing'
# user_message_c = 'https://drive.google.com/file/d/1pCwBLqmA4aUDdGZaF5t7YvxvGBl1gu5P/view?usp=sharing'
# user_message_keyword = '放假 選課'
# user_message_keyword_city_loca = '新北市蘆洲區 臺北市信義區'
# user_message_time_com = '60'
# user_message_j = 'https://drive.google.com/file/d/1d3c2vpNHrC2WImfCdiPuJuk1bLDrPzSN/view?usp=sharing'
# user_message_ID = '78d1a08a24de0fc551f6deea9cc307259ec875eb5ed2a944cedcd545f7e83a82@group.calendar.google.com'

# delet_data_of_school(user_id)  # 成功

# basic_information(user_id, user_message_basis)  # 成功
# print('basis')
# curriculum(user_id, user_message_e)  # 成功
# calendar(user_id, user_message_c,user_message_keyword)  # 成功
# daily_remind_add(user_id, user_message_remind)  # 成功
# print('remind_add')
# daily_remind_delet(user_id, user_message_remind_index)  # 成功
# remind_text = daily_remind_list(user_id)  # 成功
# print(remind_text)

# daily_tasks_add(user_id, user_message_task)  # 成功
# print('tasks_add')
# daily_tasks_delet(user_id, user_message_task_index)  # 成功
# tasks_text = daily_tasks_list(user_id)  # 成功
# print(tasks_text)

# daily_tasks_delet_masch(user_id, tast_sch)

# add_task(user_id, summary, start_time, end_time)
# check_Taipei(user_id,keyword)  # 成功
# check_Newtaipei(user_id,keyword)  # 成功
# location_weather(user_id,user_message_keyword_city_loca)  # 成功
# save_communication_time(user_id,user_message_time_com)  # 成功
# save_json(user_id,user_message_j)  # 成功
# save_ID(user_id,user_message_ID)  # 成功