# -*- coding: utf-8 -*-

from flask import *
import mysql.connector
import jwt
from jwt.exceptions import DecodeError
from datetime import datetime
import mysql.connector
from mysql.connector import pooling
import requests

app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.config["JSONIFY_MIMETYPE"] = 'application/json; charset=utf-8'
app.config ['JSON_SORT_KEYS'] = False
secret_key = "jasonkey"


# 設定 MySQL 連接池參數
db_config = {
    "pool_name": "mypool",
    "pool_size": 10,
    "host": "localhost",
    "user": "jason",
    "password": "12tina28",
    "database": "stage2",
    "charset": "utf8",
}

# 創建 MySQL 連接池
connection_pool = pooling.MySQLConnectionPool(**db_config)



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
    connection = connection_pool.get_connection()
    try:
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
                cursor = connection.cursor(dictionary=True)
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
    finally:
        # 釋放連接回連接池
        connection.close()

@app.route("/api/attraction/<attractionId>")
def api_attraction_id(attractionId):
    connection = connection_pool.get_connection()
    try:
        try:
            # 嘗試將 attractionId 轉為整數
            attraction_id = int(attractionId)
        except ValueError:
            # 如果id錯誤的話回傳400
            return jsonify({"error":True, "message=":"請提供正確景點編號"}), 400

        query_param={}

        query = "SELECT * FROM attractions WHERE id = %(attraction_id)s"
        query_param["attraction_id"] = attraction_id
        
        cursor = connection.cursor()
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

        #let response data can sort as we want
        json_data = json.dumps(response_data, ensure_ascii=False, sort_keys=False, indent=None)
        response = Response(json_data, content_type="application/json; charset=utf-8")
        
        return response
        #return jsonify(response_data, sort_keys=False), 200, {'Content-Type': 'application/json; charset=utf-8'}
    finally:
        connection.close()



@app.route("/api/mrts")
def api_mrts():
    connection = connection_pool.get_connection()
    try:
        try:
            cursor = connection.cursor()
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
    finally:
        # 釋放連接回連接池
        connection.close()
    

#會員API
@app.route("/api/user", methods=["POST"])
def api_user():
    connection = connection_pool.get_connection()
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            cursor.close()

            if existing_user:
                return jsonify({"error":"Email already exist"}), 400
            
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
            connection.commit()
            cursor.close()

            return jsonify({"ok": True}), 200
        except Exception as e:
            return jsonify({"error":True,"message":"Internal Error"}), 500
    finally:
        # 釋放連接回連接池
        connection.close()
     

@app.route("/api/user/auth", methods=["PUT","GET"])
def api_login():
    connection = connection_pool.get_connection()
    try:
        if request.method == "PUT":
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            cursor = connection.cursor()
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
    finally:
        connection.close()


#預定行程 booking API

@app.route("/api/booking", methods=["GET","POST","DELETE"])
def api_booking():
    connection = connection_pool.get_connection()
    try:
        token = str(request.headers.get("Authorization"))
        #拿到userid
        try:
            user_info = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id=user_info.get("id")
        except Exception as e:
            print("user not login",e)
        if token == "null":
            return jsonify({"error":True,"message":"Please login first"}),403
        if request.method == "GET":
            try:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT s.attractionId, s.date, s.time, s.price, a.name, a.address, a.files
                    FROM schedules s
                    JOIN attractions a ON s.attractionId = a.id
                    WHERE s.user_id = %s
                """, (user_id,))
                schedule_info = cursor.fetchone()
                cursor.close()
                if schedule_info is None:
                    return jsonify({"data":"null"})
                else:
                    image_list = schedule_info[6].strip('[]').replace('"', '').split(', ')
                    correct_date = schedule_info[1].strftime("%Y-%m-%d")

                    responsedata={
                        "data":{
                            "attraction":{
                                "id": schedule_info[0],
                                "name": schedule_info[4],
                                "address": schedule_info[5],
                                "image": image_list[0]
                            },
                        "date": correct_date,
                        "time": schedule_info[2],
                        "price": schedule_info[3]
                        }
                    }
                    return jsonify(responsedata),200
            except Exception as e:
                return jsonify({"error":str(e)})

        elif request.method == "POST":
            try:
                data=request.get_json()
                attractionId=data.get("attractionId")
                date=data.get("date")
                time=data.get("time")
                price=data.get("price")
                cursor = connection.cursor()

                #判斷要新增還是更改行程
                cursor.execute("SELECT COUNT(*) FROM schedules WHERE user_id = %s", (user_id,))
                count=cursor.fetchone()[0]
                if count ==0:
                    cursor.execute("INSERT INTO schedules (user_id, attractionId, date, time, price) VALUES (%s, %s, %s, %s, %s)", (user_id, attractionId, date, time, price))
                else:
                    cursor.execute("UPDATE schedules SET attractionId = %s, date = %s, time = %s, price = %s WHERE user_id = %s", (attractionId, date, time, price, user_id))
                connection.commit()
                cursor.close()
                print("已新增資料")
                return jsonify({"ok":True})
            except Exception as e:
                return jsonify({"error":True,"message":str(e)})


        elif request.method == "DELETE":
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM schedules WHERE user_id = %s", (user_id,))
                connection.commit()
                cursor.close()
                return jsonify({"ok":True})
            except Exception as e:
                print(e)
                return jsonify({"error":True,"message":str(e)})
    finally:
        connection.close()
     



#order API
@app.route("/api/orders", methods=["POST"])
def api_orders():
    connection = connection_pool.get_connection()
    try:
        token = str(request.headers.get("Authorization"))
        #拿到userid
        try:
            user_info = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id=user_info.get("id")
        except Exception as e:
            print("user not login",e)
        if token == "null":
            return jsonify({"error":True,"message":"Please login first"}),403
        
        if request.method=="POST":
            #前端BODY裡面的資料
            try:
                data=request.get_json()
                primekey=data.get("prime")
                order=data.get("order")
                contact=data.get("contact")
                price=order.get("price")
                trip=order.get("trip")
                date=order.get("date")
                time=order.get("time")
                id=trip.get("id")
                attractionName=trip.get("name")
                address=trip.get("address")
                image=trip.get("image")
                name=contact.get("name")
                email=contact.get("email")
                phone=contact.get("phone")
                status="unpaid"
                timenow=datetime.now()
                order_num=timenow.strftime("%Y%m%d%M%S")
                order_num=order_num.replace("/","")
                cursor = connection.cursor()
                sql = """INSERT INTO orders (prime, price, attraction_id, attraction_name, attraction_address, attraction_image, trip_date, trip_time, contact_name, contact_email, contact_phone, payment_status, order_number)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql,(primekey,price,id,attractionName,address,image,date,time,name,email,phone,status,order_num))
                connection.commit()
                cursor.close()
                print(primekey,price,id,attractionName,address,image,date,time,name,email,phone,status)
            except Exception as e:
                print("Request格式錯誤",e)
                return jsonify({"error":True,"message":"訂單建立失敗"})
            #向第三方支付打API
            request_data={
                "prime":primekey,
                "partner_key":"partner_xojIhwZCO89VZF7U4KC6s1PgnR5Oek8BdHW7aHuTyztbrJKhynoPElFl",
                "merchant_id":"jasonlin_CTBC",
                "amount":price,
                "details":"旅遊行程",
                "cardholder":{
                    "phone_number":phone,
                    "name":name,
                    "email":email
                }
            }
            api_url="https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
            response=requests.post(api_url,json=request_data,headers={'Content-Type': 'application/json','x-api-key':"partner_xojIhwZCO89VZF7U4KC6s1PgnR5Oek8BdHW7aHuTyztbrJKhynoPElFl"})
            if response.status_code==200:
                #更新資料庫狀態
                cursor = connection.cursor()
                cursor.execute("UPDATE orders SET payment_status='paid' WHERE order_number=%s", (order_num,))
                connection.commit()
                cursor.close()
                response_data={
                    "data":{
                        "number":order_num,
                        "payment":{
                            "status":0,
                            "message":"付款成功"
                        }
                    }
                }
                return jsonify(response_data),200
            else:
                print("付款失敗")
                response_data={
                    "data":{
                        "number":order_num,
                        "payment":{
                            "status":1,
                            "message":"付款失敗"
                        }
                    }
                }

                return jsonify(response_data),200
    finally:
        connection.close()
     
     
@app.route("/api/order/<orderNumber>")
def api_order(orderNumber):
    connection = connection_pool.get_connection()
    try:
        token = str(request.headers.get("Authorization"))
        #拿到userid
        try:
            user_info = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id=user_info.get("id")
        except Exception as e:
            print("user not login",e)
        if token == "null":
            return jsonify({"error":True,"message":"Please login first"}),403
        query_param={}
        query = "SELECT * FROM orders WHERE order_number = %(orderNumber)s"
        query_param["orderNumber"]=orderNumber
        cursor = connection.cursor()
        cursor.execute(query,query_param)
        order_detail=cursor.fetchone()
        cursor.close()
        if not order_detail:
            return jsonify({"data":"null"})
        else:
            response_data={
                "data":{
                    "number":order_detail[13],
                    "price":order_detail[2],
                    "trip":{
                        "attraction":{
                            "id":order_detail[3],
                            "name":order_detail[4],
                            "address":order_detail[5],
                            "image":order_detail[6]
                        },
                        "date":order_detail[7],
                        "time":order_detail[8]
                    },
                    "contact":{
                        "name":order_detail[9],
                        "email":order_detail[10],
                        "phone":order_detail[11]
                    },
                    "status":1
                }
            }
            print(order_detail)
            json_data = json.dumps(response_data, ensure_ascii=False, sort_keys=False, indent=None)
            response = Response(json_data, content_type="application/json; charset=utf-8")
            return response

    finally:
        connection.close()



app.run(host="0.0.0.0", port=5000)