# -*- coding: utf-8 -*-

from flask import *
import mysql.connector

app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False  # 避免换行时产生的乱码
app.config["JSONIFY_MIMETYPE"] = 'application/json; charset=utf-8'


try:
    db = mysql.connector.connect(
        host="NO-20230525204903",
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
        page = request.args.get('page', type=int)
        keyword = request.args.get('keyword', type=str)

        # 計算 OFFSET 值
        offset = 12 * (page - 1) if page > 0 else 0

        # 建立 SQL 查詢
        query = "SELECT * FROM attractions"
        if keyword:
            query += f" WHERE name LIKE '%{keyword}%'"
        query += f" LIMIT 12 OFFSET {offset};"

        cursor = db.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        response_data = {
            "results": results
        }

        return jsonify(response_data), 200, {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        error_response = {
            "error": str(e)
        }
        return jsonify(error_response), 500, {'Content-Type': 'application/json; charset=utf-8'}


@app.route("/api/attraction/<attractionId>")
def api_attraction_id(attractionId):
    try:
        # 嘗試將 attractionId 轉為整數
        attraction_id = int(attractionId)
    except ValueError:
        # 如果id錯誤的話回傳400
        return jsonify({"error": "Invalid attraction ID"}), 400

    cursor = db.cursor()
    query = f"SELECT * FROM attractions WHERE id={attraction_id}"
    cursor.execute(query)
    attraction = cursor.fetchone()
    cursor.close()

    if not attraction:
        # 如果景點不存在，回傳500錯誤
        return jsonify({"error": "Attraction not found"}), 500

    # 构建景点数据
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
        "images": [attraction[15]]
    }

    response_data = {
        "data": attraction_data
    }

    return jsonify(response_data), 200, {'Content-Type': 'application/json; charset=utf-8'}
	

@app.route("/api/mrts")
def api_mrts():
    try:
        cursor = db.cursor()
        # 查询捷運站名稱和週邊景點數量
        query = """
            SELECT MRT, COUNT(*) as num_attractions
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
        
        response_data = {"mrt_names": mrt_names}

        response = jsonify(response_data)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

        # 返回捷運站名稱列表
        return response

    except Exception as e:
        # 報錯回傳 500 
        error_message = str(e)
        return jsonify({"error": error_message}), 500



app.run(host="0.0.0.0", port=3000)