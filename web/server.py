import json

from flask import Flask, render_template, request, jsonify
import aiohttp
from lxml.html import fromstring
from flask_lt import run_with_lt

app = Flask(__name__)
run_with_lt(app, subdomain="dacquoise")
with open("database/gorogo_t2n.json", encoding="utf-8") as f:
    gorogo_t2n = json.load(f)
with open("database/gorogo_n2t.json", encoding="utf-8") as f:
    gorogo_n2t = json.load(f)
with open("database/kakusin.json", encoding="utf-8") as f:
    kakusin = json.load(f)


@app.route("/")
async def index():
    param = {"word": "", "mode": "english"}
    if (mode := request.args.get('mode')) is not None:
        param["mode"] = mode
        if (query := request.args.get("query")) is not None:
            session = aiohttp.ClientSession()
            param["word"] = query
            if mode == "english":  # 英単語
                # weblioから意味を取得
                headers = {"User-Agent": "iPhone"}
                resp = await session.get(
                    f"https://ejje.weblio.jp/content/{query}?smtp=smp_apl_ios",
                    headers=headers
                )
                html = await resp.text()
                results = fromstring(html).xpath("//script[@id = 'main-explanation']")
                if results:
                    data = json.loads(results[0].text)
                    if "explanation" in data:
                        param["weblio"] = data["explanation"]["content"]

                # gogen-edjから語源を取得
                resp = await session.get(
                    f"https://gogen-ejd.info/{query}/"
                )
                html = await resp.text()
                results = fromstring(html).xpath("//div[@class='su-box-content su-u-clearfix su-u-trim']")
                if results:  # 登録された単語の場合
                    derivation = results[0].text_content().strip().replace("⇒", "⇒。").split("。")
                    related = results[1].text_content().strip().split("\n")
                    related_meta = [{"label": word, "raw": word.split('（')[0].strip()} for word in related]
                    param["gogen_edj"] = [derivation, related_meta]
            else:  # 古文単語
                param["gorogo"] = {}
                param["gorogo"]["tit"] = f"https://gorogo.net/grgnetwp/wp-content/mingorodata2/title/{query}a-ktng-ttl.png"
                param["gorogo"]["fig"] = f"https://gorogo.net/grgnetwp/wp-content/mingorodata2/fig/{query}a-ktng-fig.png"
                param["gorogo"]["imi"] = f"https://gorogo.net/grgnetwp/wp-content/mingorodata2/imi/a/{query}a-ktng-imi.png"
                param["gorogo"]["goro"] = f"https://gorogo.net/grgnetwp/wp-content/mingorodata2/goro/a/{query}a-ktng-gro.png"
                word = gorogo_n2t[query]
                param["word"] = word
                if word in kakusin:
                    param["kakusin"] = kakusin[word]

            await session.close()
    return render_template("index.html", **param)


@app.route("/complete")
async def complete():  # 自動補完用
    if "mode" not in request.args or "query" not in request.args:
        return jsonify([])
    mode = request.args.get('mode')
    query = request.args.get('query')
    session = aiohttp.ClientSession()
    if mode == "english":  # 英単語
        headers = {"X-Weblio-Turbo-CF": "y1fOhjQbsOSFxRdz"}
        resp = await session.get(
            f"https://ejje.weblio.jp/api/turbo/explanation?query={query}",
            headers=headers
        )
        words = await resp.json(content_type=None)  # ignore text/javascript on decoding
        await session.close()
        return jsonify([{"label": word["lennma"], "category": word["explanationDescription"], "raw": word["lennma"]} for word in words])
    else:  # 古文単語
        words = [{"label": key, "raw": gorogo_t2n[key]} for key in gorogo_t2n.keys() if key.startswith(query)]
        await session.close()
        return jsonify(words)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
