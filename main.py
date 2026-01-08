from flask import Flask, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- 3.0 版本 UI：增加海报墙和详情跳转 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no, viewport-fit=cover">
    <!-- 关键：解决豆瓣图片不显示的问题 -->
    <meta name="referrer" content="no-referrer">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>豆瓣高分电影</title>
    <style>
        body { font-family: -apple-system, sans-serif; background-color: #f2f2f7; margin: 0; padding-bottom: 80px; }
        .header { padding: 40px 20px 20px; background: #fff; border-bottom: 1px solid #d1d1d6; }
        h1 { margin: 0; font-size: 28px; font-weight: 800; color: #1c1c1e; }
        p { color: #8e8e93; margin: 5px 0 0; }
        .movie-list { padding: 15px; }
        .movie-card { 
            display: flex; background: white; border-radius: 12px; margin-bottom: 15px; 
            overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-decoration: none; color: inherit;
        }
        .movie-card:active { background: #e5e5ea; }
        .movie-poster { width: 100px; height: 140px; object-fit: cover; }
        .movie-info { padding: 12px; flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
        .movie-title { font-size: 17px; font-weight: bold; color: #000; margin-bottom: 5px; }
        .movie-meta { font-size: 13px; color: #8e8e93; line-height: 1.4; }
        .rating-box { display: flex; align-items: center; margin-top: 5px; }
        .star { color: #ff9500; font-size: 14px; margin-right: 4px; }
        .score { font-weight: bold; color: #ff9500; font-size: 15px; }
        .quote { font-style: italic; font-size: 12px; color: #48484a; margin-top: 8px; border-left: 2px solid #34c759; padding-left: 8px; }
        .refresh-btn { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
                       background: #34c759; color: white; padding: 12px 40px; 
                       border-radius: 25px; font-weight: 600; border: none; font-size: 16px;
                       box-shadow: 0 4px 15px rgba(52,199,89,0.4); z-index: 1000; }
        #loading { text-align: center; padding: 50px; color: #8e8e93; }
    </style>
</head>
<body>
    <div class="header">
        <h1>豆瓣电影 Top250</h1>
        <p>自用高分电影监控助手</p>
    </div>
    
    <div id="loading">正在连接豆瓣服务器...</div>
    <div class="movie-list" id="content"></div>

    <button class="refresh-btn" onclick="fetchData()">刷新榜单</button>

    <script>
        async function fetchData() {
            document.getElementById('loading').style.display = 'block';
            try {
                const res = await fetch('/api/scrape');
                const result = await res.json();
                if(result.success) {
                    const html = result.data.map(m => `
                        <a href="${m.link}" class="movie-card" target="_blank">
                            <img src="${m.img}" class="movie-poster" alt="海报">
                            <div class="movie-info">
                                <div>
                                    <div class="movie-title">${m.title}</div>
                                    <div class="movie-meta">${m.info}</div>
                                    <div class="rating-box">
                                        <span class="star">★</span>
                                        <span class="score">${m.score}</span>
                                        <span style="font-size:12px; color:#8e8e93; margin-left:8px;">(${m.votes}人评价)</span>
                                    </div>
                                </div>
                                ${m.quote ? `<div class="quote">“${m.quote}”</div>` : ''}
                            </div>
                        </a>
                    `).join('');
                    document.getElementById('content').innerHTML = html;
                }
            } catch (e) { alert('抓取失败，请检查网络或稍后再试'); }
            document.getElementById('loading').style.display = 'none';
        }
        window.onload = fetchData;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/scrape')
def scrape():
    # 爬取豆瓣电影 Top 250 第一页
    url = "https://movie.douban.com/top250"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        movie_data = []
        items = soup.select('ol.grid_view li')
        
        for item in items:
            title = item.select_one('.title').text
            img = item.select_one('.pic img')['src']
            score = item.select_one('.rating_num').text
            votes = item.select_one('.star span:last-child').text.replace('人评价', '')
            info = item.select_one('.bd p').text.strip().split('\\n')[0]
            link = item.select_one('.hd a')['href']
            quote = item.select_one('.inq').text if item.select_one('.inq') else ""
            
            movie_data.append({
                "title": title,
                "img": img,
                "score": score,
                "votes": votes,
                "info": info,
                "link": link,
                "quote": quote
            })

        return jsonify({"success": True, "data": movie_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
