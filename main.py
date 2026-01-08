from flask import Flask, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup
import os
import random

app = Flask(__name__)

# --- V7.0：双频道分类版（新增上映时间 + 华语聚合） ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>影讯监控</title>
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
            background-color: var(--ios-bg); margin: 0; padding-bottom: 100px;
        }
        
        /* 顶部毛玻璃页眉 */
        .header { 
            padding: 50px 20px 15px; 
            background: rgba(255,255,255,0.85); 
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border-bottom: 0.5px solid #d1d1d6; 
            position: sticky; top: 0; z-index: 100;
        }
        h1 { margin: 0 0 15px 0; font-size: 26px; font-weight: 800; }

        /* iOS 风格切换开关 */
        .selector {
            display: flex; background: #e3e3e8; padding: 2px; border-radius: 9px; margin-bottom: 5px;
        }
        .selector-item {
            flex: 1; text-align: center; padding: 6px 0; font-size: 13px; font-weight: 600;
            border-radius: 7px; color: #3a3a3c; transition: 0.2s;
        }
        .selector-item.active {
            background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.12); color: #000;
        }

        .movie-list { padding: 15px; }
        .movie-card { 
            display: flex; align-items: center;
            background: white; border-radius: 16px; 
            margin-bottom: 12px; padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04); 
            text-decoration: none; color: inherit;
        }
        .movie-card:active { background: #e5e5ea; transform: scale(0.98); }
        
        .rank-badge {
            width: 36px; height: 36px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; font-weight: 800; color: white; margin-right: 15px;
            flex-shrink: 0; background: #d1d1d6;
        }
        .rank-1 { background: var(--gold); }
        .rank-2 { background: var(--silver); }
        .rank-3 { background: var(--bronze); }
        
        .info-content { flex: 1; min-width: 0; }
        .movie-title { font-size: 17px; font-weight: 700; color: #1c1c1e; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .score-box { display: flex; align-items: center; margin-bottom: 6px; }
        .score-num { font-weight: 800; color: #ff9500; font-size: 14px; margin-right: 6px; }
        
        .meta { font-size: 12px; color: #8e8e93; line-height: 1.5; margin-bottom: 2px; }
        .release-date { display: inline-block; background: #f2f2f7; color: #5856d6; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 11px; margin-top: 4px; }
        
        .refresh-btn { 
            position: fixed; bottom: 35px; left: 50%; transform: translateX(-50%); 
            background: var(--ios-blue); color: white; 
            padding: 14px 45px; border-radius: 30px; 
            font-weight: 600; border: none; font-size: 16px;
            box-shadow: 0 8px 20px rgba(0,122,255,0.3); z-index: 1000; 
        }
        #loading { text-align: center; padding: 100px 20px; color: #8e8e93; }
    </style>
</head>
<body>
    <div class="header">
        <h1>影讯监控</h1>
        <div class="selector">
            <div id="btn-all" class="selector-item active" onclick="switchTab('all')">全部热映</div>
            <div id="btn-cn" class="selector-item" onclick="switchTab('cn')">华语精选</div>
        </div>
    </div>
    <div id="loading">正在同步豆瓣影讯...</div>
    <div id="content" class="movie-list"></div>
    <button class="refresh-btn" onclick="fetchData()">刷新数据</button>

    <script>
        let allMovies = [];
        let currentTab = 'all';

        async function fetchData() {
            const content = document.getElementById('content');
            const loading = document.getElementById('loading');
            loading.style.display = 'block';
            content.innerHTML = '';
            try {
                const res = await fetch('/api/scrape');
                const result = await res.json();
                if(result.success) {
                    allMovies = result.data;
                    renderList();
                } else {
                    content.innerHTML = `<div style="text-align:center; margin-top:50px; color:#8e8e93;">${result.error}</div>`;
                }
            } catch (e) { content.innerHTML = '<div style="text-align:center; margin-top:50px; color:#8e8e93;">网络繁忙</div>'; }
            loading.style.display = 'none';
        }

        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('btn-all').classList.toggle('active', tab === 'all');
            document.getElementById('btn-cn').classList.toggle('active', tab === 'cn');
            renderList();
        }

        function renderList() {
            const content = document.getElementById('content');
            let filtered = currentTab === 'all' ? allMovies : allMovies.filter(m => m.is_chinese);
            
            if(filtered.length === 0) {
                content.innerHTML = '<div style="text-align:center; margin-top:50px; color:#8e8e93;">暂无此类电影上映</div>';
                return;
            }

            content.innerHTML = filtered.map((m, index) => {
                const rank = index + 1;
                let rankClass = rank <= 3 ? `rank-${rank}` : "";
                return `
                <a href="${m.link}" class="movie-card" target="_blank">
                    <div class="rank-badge ${rankClass}">${rank}</div>
                    <div class="info-content">
                        <div class="movie-title">${m.title}</div>
                        <div class="score-box">
                            <span class="score-num">${m.score === '0' ? '新片无评分' : '★ ' + m.score}</span>
                            <span class="release-date">📅 ${m.release_date} 上映</span>
                        </div>
                        <div class="meta">${m.region} · ${m.duration}</div>
                        <div class="meta" style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${m.actors}</div>
                    </div>
                </a>
                `;
            }).join('');
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
    # 豆瓣正在上映
    url = "https://movie.douban.com/cinema/nowplaying/beijing/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        movie_data = []
        items = soup.select('div#nowplaying li.list-item')
        
        for item in items:
            try:
                region = item.get('data-region', '')
                # 华语电影识别逻辑
                is_cn = any(x in region for x in ["中国大陆", "中国香港", "中国台湾"])
                
                movie_data.append({
                    "title": item.get('data-title', '未知'),
                    "score": item.get('data-score', '0'),
                    "duration": item.get('data-duration', ''),
                    "region": region,
                    "release_date": item.get('data-release', '待定'), # 上映时间
                    "actors": item.get('data-actors', ''),
                    "is_chinese": is_cn,
                    "link": f"https://movie.douban.com/subject/{item.get('id')}/"
                })
            except: continue
            
        # 默认按评分降序
        movie_data.sort(key=lambda x: float(x['score']), reverse=True)
        
        return jsonify({"success": True, "data": movie_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
