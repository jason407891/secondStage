# -*- coding: utf-8 -*-

from flask import *
import mysql.connector
import jwt
from jwt.exceptions import DecodeError



app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.config["JSONIFY_MIMETYPE"] = 'application/json; charset=utf-8'
app.config ['JSON_SORT_KEYS'] = False
secret_key = "jasonkey"



try:
    db = mysql.connector.connect(
        host="localhost",
        user="jason",
        password="12tina28",
        database="stage2",
        charset="utf8"
    )
except mysql.connector.Error as err:
    print("Error:", err)


# Pages
@app.route("/")
def index():
	return render_template("index.html")
@app.route("/attraction/<id>")
def attraction(id):
	return render_template("attraction.html")
@app.route("/booking")
def booking():
	return render_template("booking.html")
@app.route("/thankyou")
def thankyou():
	return render_template("thankyou.html")


@app.route("/api/attractions")
def api_attractions():
    try:
        # 取得 URL 參數中的 page 和 keyword
        page = request.args.get('page',type= int)
        keyword = request.args.get('keyword', type=str)
        if page>=0:
            # 計算 OFFSET 值
            offset = 12 * page if page >= 0 else 0

            # 建立 SQL 查詢
            query = "SELECT id,name,CAT as category,description,address,direction as transport,MRT as mrt,latitude as lat,longitude as lng,files as images FROM attractions"
            query_param={}
            
            if keyword:
                query += " WHERE (`MRT` = %(keyword)s OR `name` LIKE %(keyword_like)s)"
                query_param['keyword'] = keyword
                query_param['keyword_like'] = f"%{keyword}%"
            query += " LIMIT 12 OFFSET %(offset)s"
            query_param['offset'] = offset
            cursor = db.cursor(dictionary=True)
            cursor.execute(query, query_param)
            results = cursor.fetchall()

            if not results:
                 nextpage = None
            else:
                 nextpage = page+1
            for result in results:
                result['images']=json.loads(result["images"])
            cursor.close()
            response_data = {
                "nextPage":nextpage,
                "data":results
            }
            
            json_data = json.dumps(response_data, ensure_ascii=False, sort_keys=False, indent=None)
            response = Response(json_data, content_type="application/json; charset=utf-8")
            
            return response
            #return jsonify(response_data, sort_keys=False), 200, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            response = {
                "error":True,
                "message":"please enter page"
            }
            return jsonify(response), 500, {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        error_response = {
            "error":True,
            "message":str(e)
        }
        return jsonify(error_response), 500, {'Content-Type': 'application/json; charset=utf-8'}


@app.route("/api/attraction/<attractionId>")
def api_attraction_id(attractionId):
    try:
        # 嘗試將 attractionId 轉為整數
        attraction_id = int(attractionId)
    except ValueError:
        # 如果id錯誤的話回傳400
        return jsonify({"error":True, "message=":"請提供正確景點編號"}), 400

    query_param={}

    query = "SELECT * FROM attractions WHERE id = %(attraction_id)s"
    query_param["attraction_id"] = attraction_id
    
    cursor = db.cursor()
    cursor.execute(query, query_param)

    attraction = cursor.fetchone()
    cursor.close()

    if not attraction:
        # 如果景點不存在，回傳500錯誤
        return jsonify({"error":True, "message=":"請提供正確景點編號"}), 400

    # 景點資料回傳
    attraction_data = {
        "id": attraction[0],
        "name": attraction[1],
        "category": attraction[12],
        "description": attraction[18],
        "address": attraction[20],
        "transport": attraction[3],
        "mrt": attraction[9],
        "lat": attraction[17],
        "lng": attraction[5],
        "images":json.loads(attraction[15])
    }

    response_data = {
        "data": attraction_data
    }
    
    json_data = json.dumps(response_data, ensure_ascii=False, sort_keys=False, indent=None)
    response = Response(json_data, content_type="application/json; charset=utf-8")
    
    return response
    #return jsonify(response_data, sort_keys=False), 200, {'Content-Type': 'application/json; charset=utf-8'}
	

@app.route("/api/mrts")
def api_mrts():
    try:
        cursor = db.cursor()
        # 查询捷運站名稱和週邊景點數量
        query = """
            SELECT MRT , COUNT(*) as num_attractions
            FROM attractions
            WHERE MRT IS NOT NULL
            GROUP BY MRT
            ORDER BY num_attractions DESC
            LIMIT 40
        """
        cursor.execute(query)

        results = cursor.fetchall()

        # 按照週邊景點數量由大到小排序
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

        # 取得前 40 筆捷運站名稱列表
        mrt_names = [result[0] for result in sorted_results]
        
        response_data = {"data": mrt_names}

        response = jsonify(response_data)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

        # 返回捷運站名稱列表
        return response

    except Exception as e:
        # 報錯回傳 500 
        error_message = str(e)
        return jsonify({"error":True,
                         "message":error_message}), 500
    

#會員API
@app.route("/api/user", methods=["POST"])
def api_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        cursor.close()

        if existing_user:
             return jsonify({"error":"Email already exist"}), 400
        
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        db.commit()
        cursor.close()

        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error":True,"message":"Internal Error"}), 500
     

@app.route("/api/user/auth", methods=["PUT","GET"])
def api_login():
    if request.method == "PUT":
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        cursor = db.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            user_info = {
                "id": user[0],
                "name": user[1],
                "email": user[2]
            }

            # 生成 JWT Token
            token = jwt.encode(user_info, secret_key, algorithm="HS256")

            return jsonify({"token": token})
        else:
            return jsonify({"error":True, "message":"帳號或是密碼輸入錯誤"}), 400
    elif request.method == "GET":
        token = request.headers.get("Authorization")
        if token=="null":
            return jsonify({"error":True,"message":"user not login"}), 200
        try:
            user_info = jwt.decode(token, secret_key, algorithms=["HS256"])
            return jsonify({"data": user_info})
        except DecodeError as e:
            return jsonify({"error":True,"message":str(e)}), 500



    
     
     
     




app.run(host="0.0.0.0", port=5000)
