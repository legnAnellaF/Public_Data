from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/widget', methods=['POST'])
def get_widget_data():
    data = request.json
    query = data.get('query')
    # 여기에 공공데이터 API 연동 로직 추가 예정
    return jsonify({
        "status": "success",
        "widget": {
            "chart": {"type": "bar", "labels": ["PM10", "PM2.5"], "data": [30, 15]}
        }
    })

if __name__ == '__main__':
    app.run(port=8000)
