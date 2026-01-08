from flask import Flask, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup
import os
import random

app = Flask(__name__)

# --- V6.0：精致榜单版（无图、高级感序号） ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>热映榜单</title>
    <style>
        :root {
            --ios-bg: #f2f2f7;
            --ios-blue: #007aff;
            --gold: linear-gradient(135deg, #ffd700, #ffae00);
            --silver: linear-gradient(135deg, #c0c0c0, #939393);
            --bronze: linear-gradient(135deg, #cd7f32, #a0522d);
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif; 
            background-color: var(--ios-bg); 
            margin: 0; padding-bottom: 100px;
        }
        .header { 
            padding: 50px 20px 20px; 
            background: rgba(255,255,255,0.85); 
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border-bottom: 0.5px solid #d1d1d6; 
            position: sticky; top: 0; z-index: 100;
        }
        h1 { margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }
        .movie-list { padding: 15px; }
        .movie-card { 
            display: flex; align-items: center;
            background: white; border-radius: 16px; 
            margin-bottom: 12px; padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04); 
            text-decoration: none; color: inherit;
        }
        .movie-card:active { background: #e5e5ea; transform: scale(0.98); transition: 0.1s; }
        
        /* 精致序号设计 */
        .rank-badge {
            width: 40px; height: 40px;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 18px; font-weight: 800;
            color: white; margin-right: 15px;
            flex-shrink: 0;
            background: #d1d1d6; /* 默认灰色 */
        }
        .rank-1 { background: var(--gold); box-shadow: 0 4px 10px rgba(255,174,0,0.3); }
        .rank-2 { background: var(--silver); }
        .rank-3 { background: var(--bronze); }
        
        .info-content { flex: 1; min-width: 0; }
        .movie-title { 
            font-size: 18px; font-weight: 700; color: #1c1c1e; 
            margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; 
        }
        .score-box { display: flex; align-items: center; margin-bottom: 4px; }
        .score-num { font-weight: 800; color: #ff9500; font-size: 15px; margin-right: 6px; }
        .meta { font-size: 12px; color: #8e8e93; line-height: 1.4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        .refresh-btn { 
            position: fixed; bottom: 35px; left: 50%; transform: translateX(-50%); 
            background: var(--ios-blue); color: white; 
            padding: 14px 45px; border-radius: 30px; 
            font-weight: 600; border: none; font-size: 17px;
            box-shadow: 0 8px 20px rgba(0,122,255,0.3); z-index: 1000; 
        }
        #loading { text-align: center; padding: 100px 20px; color: #8e8e93; }
    </style>
</head>
<body>
    <div class="header"><h1>正在热映 · 榜单</h1></div>
    <div id="loading">正在获取实时数据...</div>
    <div id="content" class="movie-list"></div>
    <button class="refresh-btn" onclick="fetchData()">刷新数据</button>

    <script>
        async function fetchData() {
            const content = document.getElementById('content');
            const loading = document.getElementById('loading');
            loading.style.display = 'block';
            try {
                const res = await fetch('/api/scrape');
                const result = await res.json();
                if(result.success) {
                    content.innerHTML = result.data.map((m, index) => {
                        const rank = index + 1;
                        let rankClass = "";
                        if(rank === 1) rankClass = "rank-1";
                        else if(rank === 2) rankClass = "rank-2";
                        else if(rank === 3) rankClass = "rank-3";

                        return `
                        <a href="${m.link}" class="movie-card" target="_blank">
                            <div class="rank-badge ${rankClass}">${rank}</div>
                            <div class="info-content">
                                <div class="movie-title">${m.title}</div>
                                <div class="score-box">
                                    <span class="score-num">${m.score === '0' ? '暂无评分' : '★ ' + m.score}</span>
                                </div>
                                <div class="meta">${m.region} · ${m.duration}</div>
                                <div class="meta">${m.actors}</div>
                            </div>
                        </a>
                        `;
                    }).join('');
                } else {
                    content.innerHTML = `<div style="padding:40px; text-align:center; color:#8e8e93;">无法获取数据<br>${result.error}</div>`;
                }
            } catch (e) {
                content.innerHTML = '<div style="padding:40px; text-align:center; color:#8e8e93;">网络超时</div>';
            }
            loading.style.display = 'none';
        }
        window.onload = fetchData;
    </script>
</body>
</html>
"""

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Referer': 'https://movie.douban.com/'
}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/scrape')
def scrape():
    # 使用北京站作为默认热映数据源
    url = "https://movie.douban.com/cinema/nowplaying/beijing/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        movie_data = []
        items = soup.select('div#nowplaying li.list-item')
        
        for item in items:
            try:
                # 过滤掉还没有评分的（通常是还未大范围公映的）可选
                movie_data.append({
                    "title": item.get('data-title', '未知'),
                    "score": item.get('data-score', '0'),
                    "duration": item.get('data-duration', ''),
                    "region": item.get('data-region', ''),
                    "actors": item.get('data-actors', ''),
                    "link": f"https://movie.douban.com/subject/{item.get('id')}/"
                })
            except: continue
            
        # 根据评分降序排序，让榜单更有意义
        movie_data.sort(key=lambda x: float(x['score']), reverse=True)
        
        return jsonify({"success": True, "data": movie_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
