import discord
from discord.ext import commands
import sqlite3
import random

# DB 연결
conn = sqlite3.connect('items.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS items 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, used INTEGER)''')
conn.commit()

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'봇이 로그인되었습니다: {bot.user}')

@bot.command()
async def 추가(ctx, item_name, count: int = 1):
    """사용법: !추가 [아이템이름] [개수] (개수를 생략하면 1개 추가)"""
    for _ in range(count):
        c.execute("INSERT INTO items (name, used) VALUES (?, 0)", (item_name,))
    
    conn.commit()
    await ctx.send(f"✅ '{item_name}' 아이템이 {count}개 추가되었습니다.")

@bot.command()
async def 뽑기(ctx):
    c.execute("SELECT id, name FROM items WHERE used = 0")
    items = c.fetchall()
    if not items:
        await ctx.send("❌ 뽑을 아이템이 없습니다! `!리셋`으로 초기화해주세요.")
        return
    chosen = random.choice(items)
    c.execute("UPDATE items SET used = 1 WHERE id = ?", (chosen[0],))
    conn.commit()
    await ctx.send(f"🎲 당첨된 아이템: **{chosen[1]}**")

@bot.command()
async def 리셋(ctx):
    c.execute("UPDATE items SET used = 0")
    conn.commit()
    await ctx.send("🔄 모든 아이템 상태가 초기화되었습니다!")

import discord
from discord.ext import commands

# 페이지네이션을 위한 뷰 클래스 정의
class ListView(discord.ui.View):
    def __init__(self, items, user_id):
        super().__init__(timeout=60) # 60초 뒤 버튼 비활성화
        self.items = items
        self.current_page = 0
        self.items_per_page = 40
        self.user_id = user_id

    def create_embed(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        chunk = self.items[start:end]
        
        embed = discord.Embed(title="📋 아이템 목록", color=discord.Color.blue())
        list_text = ""
        
        # 여기서 enumerate를 사용해 페이지별 번호(1~10)를 다시 생성합니다.
        for i, item in enumerate(chunk, start=1):
            # item[0]은 DB ID, item[1]은 이름입니다.
            list_text += f"- [{i + (self.current_page * self.items_per_page)}] {item[1]} (DB ID: {item[0]})\n"
        
        embed.description = list_text or "아이템이 없습니다."
        embed.set_footer(text=f"페이지 {self.current_page + 1} / {(len(self.items) - 1) // self.items_per_page + 1}")
        return embed
        
        embed.description = list_text or "아이템이 없습니다."
        embed.set_footer(text=f"페이지 {self.current_page + 1} / {(len(self.items) - 1) // self.items_per_page + 1}")
        return embed

    @discord.ui.button(label="◀️ 이전", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="다음 ▶️", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        if (self.current_page + 1) * self.items_per_page < len(self.items):
            self.current_page += 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

@bot.command()
async def 목록(ctx):
    c.execute("SELECT id, name FROM items WHERE used = 0")
    items = c.fetchall()
    if not items:
        await ctx.send("현재 남아있는 아이템이 없습니다.")
        return
    view = ListView(items, ctx.author.id)
    await ctx.send(embed=view.create_embed(), view=view)

@bot.command()
async def 삭제(ctx, item_id: int):
    """사용법: !삭제 [아이템ID]"""
    # 해당 ID를 가진 아이템이 있는지 확인
    c.execute("SELECT name FROM items WHERE id = ?", (item_id,))
    item = c.fetchone()
    
    if item:
        c.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        await ctx.send(f"🗑️ ID {item_id}번 아이템 '{item[0]}'이(가) 삭제되었습니다.")
    else:
        await ctx.send(f"❌ ID {item_id}번 아이템을 찾을 수 없습니다. `!목록`으로 번호를 확인하세요.")

@bot.command()
async def 수정(ctx, item_id: int, *, new_name: str):
    """사용법: !수정 [DB ID] [새로운이름]"""
    # 해당 ID를 가진 아이템이 있는지 확인
    c.execute("SELECT name FROM items WHERE id = ?", (item_id,))
    item = c.fetchone()
    
    if item:
        c.execute("UPDATE items SET name = ? WHERE id = ?", (new_name, item_id))
        conn.commit()
        await ctx.send(f"✅ ID {item_id}번 아이템이 '{item[0]}'에서 '{new_name}'(으)로 수정되었습니다.")
    else:
        await ctx.send(f"❌ ID {item_id}번 아이템을 찾을 수 없습니다. `!목록`으로 번호를 다시 확인하세요.")

import os
bot.run(os.environ['DISCORD_TOKEN'])