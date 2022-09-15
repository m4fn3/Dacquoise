import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
import json
import main
from typing import List
from lxml.html import fromstring


async def explore(interaction: discord.Interaction, session: aiohttp.ClientSession, query: str) -> None:
    """base implementation of word search"""
    # get explanations from Weblio
    headers = {"User-Agent": "iPhone"}
    resp = await session.get(
        f"https://ejje.weblio.jp/content/{query}?smtp=smp_apl_ios",
        headers=headers
    )
    html = await resp.text()
    results = fromstring(html).xpath("//script[@id = 'main-explanation']")
    if not results:  # somehow got empty content
        await interaction.response.send_message("Somehow an unknown error has occurred.")
        return
    data = json.loads(results[0].text)
    # -------------- not listed word ----------------
    if not data:
        embed = discord.Embed(title=query, color=0xff7070)
        embed.description = "英単語が見つかりません"
        results = fromstring(html).xpath("//div[@class = 'nrCntSgWrp']")
        candidates = []
        options = []
        for res in results:  # look for candidates
            word = res.xpath("div/span[@class = 'nrCntSgT']")[0].text_content().strip()
            candidates.append("{} ({})".format(
                word,
                res.xpath("div[@class = 'nrCntSgB']")[0].text_content().strip()
            ))
            options.append(discord.SelectOption(label=word, value=word))
        view = discord.ui.View()
        if candidates:  # add footer only if candidates are available
            embed.set_footer(
                text=r"⎯⎯⎯⎯⎯⎯⎯ 可能性の高い単語 ⎯⎯⎯⎯⎯⎯⎯" + "\n" + "\n".join(candidates)
            )
            view.add_item(CandidateSelector(session, options))
        await interaction.response.send_message(embed=embed, view=view)
        return

    # -------------- listed word ----------------
    # build embed
    c = int(60/len(query))
    embed = discord.Embed(title=f"[{' '*c}**{query}**{' '*c}]", color=0x70ffb7)
    embed.description =data["explanation"]["content"]
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="英単語",
        url=f"https://ejje.weblio.jp/content/{query}")
    )

    # get word derivation from gogen-ejd
    resp = await session.get(
        f"https://gogen-ejd.info/{query}/"
    )
    html = await resp.text()
    results = fromstring(html).xpath("//div[@class='su-box-content su-u-clearfix su-u-trim']")
    if results:  # listed word
        derivation = results[0].text_content().strip().replace("⇒", "⇒\n")
        related = results[1].text_content().strip().replace("\n", ", ")
        embed.set_footer(text=f"⎯⎯⎯⎯⎯⎯⎯ 語源 ⎯⎯⎯⎯⎯⎯⎯\n{derivation}\n\n⎯⎯⎯⎯⎯⎯⎯ 関連語 ⎯⎯⎯⎯⎯⎯⎯\n{related}")
        related_meta = [word.split("（")[0].strip() for word in related.split(",")]  # extract raw word
        related_meta = list(dict.fromkeys(related_meta))  # remove duplicated word from list
        options = [discord.SelectOption(label=word, value=word) for word in related_meta]
        view.add_item(discord.ui.Button(
            label="語源",
            url=f"https://gogen-ejd.info/{query}/"
        ))
        view.add_item(CandidateSelector(session, options))

    await interaction.response.send_message(embed=embed, view=view)


class CandidateSelector(discord.ui.Select):
    """Select menu of candidates"""

    def __init__(self, session: aiohttp.ClientSession, options: list) -> None:
        super().__init__(placeholder="候補から選択して検索", min_values=1, max_values=1, options=options)
        self.session = session

    async def callback(self, interaction: discord.Interaction) -> None:
        await explore(interaction, self.session, self.values[0])


class Commands(commands.Cog):
    """Commands of the Bot"""

    def __init__(self, bot: main.Core) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    @app_commands.command(name="search", description="単語の意味を検索します")
    @app_commands.describe(query="調べたい単語")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        await explore(interaction, self.session, query)

    @search.autocomplete("query")
    async def search_query(self, interaction: discord.Interaction, query: str) -> List[app_commands.Choice[str]]:
        if query == "":  # no input
            return []
        # get auto completion from Word
        headers = {"X-Weblio-Turbo-CF": "y1fOhjQbsOSFxRdz"}
        resp = await self.session.get(
            f"https://ejje.weblio.jp/api/turbo/explanation?query={query}",
            headers=headers
        )
        words = await resp.json(content_type=None)  # ignore text/javascript on decoding
        return [app_commands.Choice(name=word["lennma"], value=word["lennma"]) for word in words]


# Setup commands
async def setup(bot: main.Core) -> None:
    await bot.add_cog(Commands(bot))
