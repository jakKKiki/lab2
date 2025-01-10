import paho.mqtt.client as mqtt
import time
from PIL import Image
import numpy as np

# MQTT Broker 設定
BROKER = "test.mosquitto.org"  # 替換為你的 MQTT Broker 地址
PORT = 1883                   # MQTT 預設埠號
TOPIC_SUBSCRIBE = "Python_message"  # 訂閱主題
TOPIC_PUBLISH = "Mqtt_message"      # 發佈主題
CLIENT_ID = "Pythonclient"     # 客戶端 ID

def read_and_output_image_info(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            # 確保圖片是 RGB 模式
            if img.mode != "RGB":
                img = img.convert("RGB")
            # 獲取 RGB 資料
            rgb_array = np.array(img)
            return width, height, rgb_array
    except:
        print('Error')

# 當客戶端連接到 Broker 時觸發的事件
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("成功連接到 MQTT Broker!")
        print(f"訂閱主題: {TOPIC_SUBSCRIBE}")
        client.subscribe(TOPIC_SUBSCRIBE)  # 訂閱主題
    else:
        print(f"連接失敗，返回碼: {rc}")

# 當接收到訊息時觸發的事件
def on_message(client, userdata, msg):
    print(f"[接收] 主題: {msg.topic}, 訊息: {msg.payload.decode()}")
    width, height, image_data = read_and_output_image_info(msg.payload.decode())
    output_h_w = f'輸入圖片:{width}*{height}'
    client.publish(TOPIC_PUBLISH, output_h_w)
    print(output_h_w)
    time.sleep(0.1)  # 避免 CPU 占用過高
    chunk_size = 40
    # 將 image_data 展平成所需格式
    formatted_data = []
    for i in range(height):
        for j in range(width):
            pixel = image_data[i][j]
            formatted_data.append(','.join(map(str, pixel)))  # 將每個像素的 [R, G, B] 合併成 'R,G,B'
    # 將展平的資料組合成字串
    # formatted_string = ' '.join(formatted_data)
    # print(len(formatted_data))
    # print(formatted_data)
    # print(len(formatted_string))
    # print(formatted_string)
    # 按 chunk_size 分段發送
    
    #===================================================================
    # for i in range(0, len(formatted_data), chunk_size):
    for i in range(0, 160, chunk_size):
        end_index = i+chunk_size-1
        # if i+chunk_size>=len(formatted_data) : end_index = len(formatted_data)-1
        if i+chunk_size>159 : end_index = 159
        chunk = ' '.join(formatted_data[i:end_index])
        client.publish(TOPIC_PUBLISH, chunk)
        print(f"[發送] 已發佈訊息: {i}~{end_index} 到主題: {TOPIC_PUBLISH}")
        print(chunk)
        time.sleep(0.1)
    #===================================================================
    
    time.sleep(0.1)
    client.publish(TOPIC_PUBLISH,'結束')
    print(f"結束!!!!!")
    

# 當客戶端斷開連接時觸發的事件
def on_disconnect(client, userdata, rc):
    print("已斷開連接")

# 建立 MQTT 客戶端
client = mqtt.Client(CLIENT_ID, protocol=mqtt.MQTTv311)  # 刪除了 callback_api_version


# 設定回呼函式
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# 連接到 MQTT Broker
print("嘗試連接到 MQTT Broker...")
client.connect(BROKER, PORT, keepalive=60)

# 啟動非同步處理循環
client.loop_start()

# 發佈與接收訊息
try:
    while True:
        time.sleep(0.1)  # 避免 CPU 占用過高
        message = input("[發送] 輸入要發佈的檔案名 (輸入 'exit' 結束): ")
        if message.lower() == "exit":
            break
        width, height, image_data = read_and_output_image_info(message)
        client.publish(TOPIC_PUBLISH, f'輸入圖片:{width}*{height}')
        time.sleep(0.1)  # 避免 CPU 占用過高
        chunk_size = 60
        # 將 image_data 展平成所需格式
        formatted_data = []
        for i in range(height):
            for j in range(width):
                pixel = image_data[i][j]
                formatted_data.append(','.join(map(str, pixel)))  # 將每個像素的 [R, G, B] 合併成 'R,G,B'

        # 將展平的資料組合成字串
        formatted_string = ' '.join(formatted_data)

        # 按 chunk_size 分段發送
        for i in range(0, len(formatted_string), chunk_size):
            chunk = formatted_string[i:i + chunk_size]
            client.publish(TOPIC_PUBLISH, chunk)
            print(f"[發送] 已發佈訊息: {i} 到主題: {TOPIC_PUBLISH}")
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\n程式中止")
finally:
    # 停止客戶端
    client.loop_stop()
    client.disconnect()
    print("已關閉 MQTT 連線")
