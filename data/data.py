import json
import mysql.connector
# 讀取 JSON 檔案
with open('taipei-attractions.json', 'r', encoding='utf-8') as file:
    data = json.load(file)


db = mysql.connector.connect(
    host="NO-20230525204903",
    user="jason",
    password="12tina28",
    database="stage2"
)

# 創建資料庫表格（如果不存在）
cursor = db.cursor()
create_table_query = """
CREATE TABLE IF NOT EXISTS attractions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    rate INT,
    direction TEXT,
    date DATE,
    longitude VARCHAR(255),
    REF_WP VARCHAR(255),
    avBegin DATE,
    langinfo VARCHAR(255),
    MRT VARCHAR(255),
    SERIAL_NO VARCHAR(255),
    RowNumber VARCHAR(255),
    CAT VARCHAR(255),
    MEMO_TIME TEXT,
    POI VARCHAR(255),
    files TEXT,  -- 將 file 改為 files 欄位名稱
    idpt VARCHAR(255),
    latitude VARCHAR(255),
    description TEXT,
    avEnd DATE,
    address VARCHAR(255)
)
"""
cursor.execute(create_table_query)
db.commit()



# 解析 JSON 中的資料並插入資料庫
for entry in data['result']['results']:
    # 將 file 字串分割為陣列，並忽略大小寫
    files = [f.lower() + '.jpg' for f in entry['file'].split('.jpg') if f and not f.endswith('.mp3')]
    all_files=[]
    all_files.extend(files)
    insert_query = """
    INSERT INTO attractions (
        name, rate, direction, date, longitude, REF_WP,
        avBegin, langinfo, MRT, SERIAL_NO, RowNumber, CAT,
        MEMO_TIME, POI, files, idpt, latitude, description, avEnd, address
    ) VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    values = (
        entry['name'], entry['rate'], entry['direction'], entry['date'], entry['longitude'], entry['REF_WP'],
        entry['avBegin'], entry['langinfo'], entry['MRT'], entry['SERIAL_NO'], entry['RowNumber'], entry['CAT'],
        entry['MEMO_TIME'], entry['POI'], json.dumps(all_files), entry['idpt'], entry['latitude'], entry['description'],
        entry['avEnd'], entry['address']
    )
    cursor.execute(insert_query, values)
    db.commit()

cursor.close()
db.close()

# 印出讀取到的資料
print(data['result']['results'])