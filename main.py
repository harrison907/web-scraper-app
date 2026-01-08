# app.py
from flask import Flask, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # 允许跨域

@app.route('/')
def index():
    # 这里是 App 的前端界面代码
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/scrape')
def scrape():
    # 实际爬虫逻辑
    url = "https://m.thepaper.cn/" # 示例：爬取澎湃新闻
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 提取前 5 条新闻标题
        titles = [t.text.strip() for t in soup.find_all('h2')[:5]]
        return jsonify({"success": True, "data": titles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# 前端 HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <link rel="manifest" href="/static/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <title>我的爬虫App</title>
    <style>
        body { font-family: -apple-system, sans-serif; padding: 20px; background: #f4f4f9; }
        .card { background: white; padding: 15px; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        button { width: 100%; padding: 15px; background: #007aff; color: white; border: none; border-radius: 12px; font-size: 16px; }
    </style>
</head>
<body>
    <h1>实时数据</h1>
    <div id="content">点击下方按钮刷新</div>
    <br>
    <button onclick="fetchData()">刷新数据</button>

    <script>
        async function fetchData() {
            const res = await fetch('/api/scrape');
            const result = await res.json();
            if(result.success) {
                document.getElementById('content').innerHTML = result.data.map(item => `<div class="card">${item}</div>`).join('');
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
