import json

from flask import Flask, render_template, request, jsonify
import aiohttp
from lxml.html import fromstring

app = Flask(__name__)
with open("database/gorogo.json", encoding="utf-8") as f:
    gorogo = json.load(f)
with open("database/kakusin.json", encoding="utf-8") as f:
    kakusin = json.load(f)


@app.route("/")
async def index():
    if (mode := request.args.get('mode')) is not None and (query := request.args.get("query")) is not None:
        session = aiohttp.ClientSession()
        param = {"def": mode}
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
            print(f"https://gogen-ejd.info/{query}/")
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
            print(param)
        else:  # 古文単語
            param["gorogo"] = {}
            resp = await session.get(
                f"https://gorogo.net/mingoro/{query}/"
            )
            html = await resp.text()
            for t in ["tit", "imi", "fig", "goro"]:
                param["gorogo"][t] = fromstring(html).xpath(f"//img[@id = '{t}']")[0].get("src")
            word = fromstring(html).xpath(f"//title")[0].text.split("|")[-1].strip()
            if word in kakusin:
                param["core"] = kakusin[word]["core"]

        await session.close()
        return render_template("index.html", **param)
    return render_template("index.html")


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
        words = [{"label": key, "raw": gorogo[key]} for key in gorogo.keys() if key.startswith(query)]
        return jsonify(words)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)