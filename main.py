from flask import Flask, jsonify, render_template_string
import requests
import os
import random

app = Flask(__name__)

# --- V10.0：修复显示 Bug + 精准华语识别 + 时间排序 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>影讯监控 10.0</title>
    <style>
        :root { --ios-bg: #f2f2f7; --ios-blue: #007aff; }
        body { font-family: -apple-system, sans-serif; background-color: var(--ios-bg); margin: 0; padding-bottom: 100px; }
        
        /* 头部设计 */
        .header { 
            padding: 50px 20px 15px; background: rgba(255,255,255,0.85); 
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border-bottom: 0.5px solid #d1d1d6; position: sticky; top: 0; z-index: 100;
        }
        h1 { margin: 0 0 15px 0; font-size: 24px; font-weight: 800; }

        /* 控制区：分类与排序 */
        .controls { display: flex; flex-direction: column; gap: 8px; }
        .selector { display: flex; background: #e3e3e8; padding: 2px; border-radius: 9px; }
        .selector-item { 
            flex: 1; text-align: center; padding: 7px 0; font-size: 12px; font-weight: 600; 
            border-radius: 7px; color: #3a3a3c; transition: 0.2s; 
        }
        .selector-item.active { background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); color: #000; }

        /* 列表展示 */
        .movie-list { padding: 15px; }
        .movie-card { 
            display: flex; align-items: center; background: white; border-radius: 16px; 
            margin-bottom: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); 
            text-decoration: none; color: inherit; 
        }
        .movie-card:active { background: #e5e5ea; transform: scale(0.98); }
        
        .rank-badge { 
            width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; 
            justify-content: center; font-size: 14px; font-weight: 800; color: white; 
            margin-right: 15px; flex-shrink: 0; background: #d1d1d6; 
        }
        .top-rank { background: var(--ios-blue); }
        
        .info-content { flex: 1; min-width: 0; }
        .movie-title { font-size: 17px; font-weight: 700; color: #1c1c1e; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .row-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap; }
        .score { font-weight: 800; color: #ff3b30; font-size: 14px; }
        .date-tag { background: #f2f2f7; color: #5856d6; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        
        .actors { font-size: 12px; color: #8e8e93; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        .refresh-btn { 
            position: fixed; bottom: 35px; left: 50%; transform: translateX(-50%); 
            background: var(--ios-blue); color: white; padding: 14px 45px; 
            border-radius: 30px; font-weight: 600; border: none; font-size: 16px; 
            box-shadow: 0 8px 20px rgba(0,122,255,0.3); z-index: 1000; 
        }
        #loading { text-align: center; padding: 100px 20px; color: #8e8e93; }
    </style>
</head>
<body>
    <div class="header">
        <h1>影讯监控</h1>
        <div class="controls">
            <div class="selector">
                <div id="tab-all" class="selector-item active" onclick="updateView('tab', 'all')">全部上映</div>
                <div id="tab-cn" class="selector-item" onclick="updateView('tab', 'cn')">华语精选</div>
            </div>
            <div class="selector">
                <div id="sort-hot" class="selector-item active" onclick="updateView('sort', 'hot')">按热度/评分</div>
                <div id="sort-time" class="selector-item" onclick="updateView('sort', 'time')">按上映时间 (新→旧)</div>
            </div>
        </div>
    </div>

    <div id="loading">正在同步最新影讯...</div>
    <div id="content" class="movie-list"></div>
    <button class="refresh-btn" onclick="fetchData()">刷新数据</button>

    <script>
        let allMovies = [];
        let state = { tab: 'all', sort: 'hot' };

        async function fetchData() {
            const loading = document.getElementById('loading');
            loading.style.display = 'block';
            try {
                const res = await fetch('/api/scrape');
                const result = await res.json();
                // 修复判断逻辑：只要 result.data 存在且是数组就渲染
                if (result && Array.isArray(result.data)) {
                    allMovies = result.data;
                    renderList();
                } else {
                    document.getElementById('content').innerHTML = '<div style="text-align:center; padding:50px;">数据格式错误</div>';
                }
            } catch (e) { 
                document.getElementById('content').innerHTML = '<div style="text-align:center; padding:50px;">服务器连接失败</div>';
            }
            loading.style.display = 'none';
        }

        function updateView(type, value) {
            state[type] = value;
            if(type === 'tab') {
                document.getElementById('tab-all').classList.toggle('active', value === 'all');
                document.getElementById('tab-cn').classList.toggle('active', value === 'cn');
            } else {
                document.getElementById('sort-hot').classList.toggle('active', value === 'hot');
                document.getElementById('sort-time').classList.toggle('active', value === 'time');
            }
            renderList();
        }

        function renderList() {
            const content = document.getElementById('content');
            
            // 1. 过滤逻辑
            let list = state.tab === 'all' ? [...allMovies] : allMovies.filter(m => m.is_chinese);
            
            // 2. 排序逻辑
            if(state.sort === 'hot') {
                list.sort((a, b) => parseFloat(b.score) - parseFloat(a.score));
            } else {
                list.sort((a, b) => new Date(b.release_date.replace('大陆上映','')) - new Date(a.release_date.replace('大陆上映','')));
            }

            if(list.length === 0) {
                content.innerHTML = `<div style="text-align:center; padding:50px; color:#999;">暂无相关数据</div>`;
                return;
            }

            content.innerHTML = list.map((m, index) => `
                <a href="${m.link}" class="movie-card" target="_blank">
                    <div class="rank-badge ${index < 3 ? 'top-rank' : ''}">${index + 1}</div>
                    <div class="info-content">
                        <div class="movie-title">${m.title}</div>
                        <div class="row-meta">
                            <span class="score">${parseFloat(m.score) > 0 ? '★ ' + m.score : '新片待定'}</span>
                            <span class="date-tag">📅 ${m.release_date}</span>
                        </div>
                        <div class="actors">${m.actors}</div>
                    </div>
                </a>
            `).join('');
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
    url = "https://i.maoyan.com/ajax/movieOnInfoList"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        raw_list = data.get('movieList', [])
        
        movie_data = []
        for m in raw_list:
            # --- 改进华语识别逻辑 ---
            pub_desc = m.get('pubDesc', '') # 例如 "2025-12-19大陆上映"
            ver = m.get('ver', '')         # 例如 "国语 2D"
            # 如果发布描述包含“大陆”或者版本包含“国语”，认定为华语片
            is_cn = ("大陆" in pub_desc) or ("国语" in ver)
            
            # 提取纯日期用于排序 (例如从 "2025-12-19大陆上映" 提取 "2025-12-19")
            raw_date = m.get('rt', '2026-01-01')
            
            movie_data.append({
                "title": m.get('nm', '未知'),
                "score": str(m.get('sc', 0)),
                "release_date": raw_date,
                "actors": m.get('star', '主演信息暂无'),
                "is_chinese": is_cn,
                "link": f"https://i.maoyan.com/movie/{m.get('id')}"
            })
            
        return jsonify({"success": True, "data": movie_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "data": []})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
