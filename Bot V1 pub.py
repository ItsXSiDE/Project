import discord
from discord.ext import commands
from collections import defaultdict
from datetime import timedelta
from discord.utils import utcnow

# Tentukan intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Pastikan intents untuk anggota diaktifkan

bot = commands.Bot(command_prefix="!", intents=intents)

blocked_words = [
    "suicide", "kill", "rape","terrorist", "howak", "palestine", "israel", "taiwan", "hitam", "bobrok", "jawa", "ireng", "yatim"
]

# Batas peringatan sebelum timeout dan ban
warning_limit_timeout = 3  
timeout_limit = 3  # Batas timeout sebelum di-ban

# Dictionary untuk mencatat jumlah peringatan dan timeout per pengguna
user_warnings = defaultdict(int)
user_timeouts = defaultdict(int)

# Fungsi untuk membuat embed
def create_embed(title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

@bot.event
async def on_ready():
    print(f"Bot berhasil login sebagai {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if any(blocked_word in message.content.lower() for blocked_word in blocked_words):
        await message.delete()
        embed = create_embed(
            title="Pesan Dihapus",
            description=f"{message.author.mention}, Pesan yang kamu kirim mengandung kata yang sensitif."
        )
        await message.channel.send(embed=embed)

        user_warnings[message.author.id] += 1
        warning_count = user_warnings[message.author.id]

        if warning_count >= warning_limit_timeout:
            await timeout_user(message)
        else:
            await send_warning(message, warning_count)

    await bot.process_commands(message)

async def timeout_user(message):
    timeout_until = utcnow() + timedelta(minutes=60)
    try:
        await message.author.timeout(timeout_until, reason="Melebihi batas peringatan")

        user_timeouts[message.author.id] += 1
        current_timeout = user_timeouts[message.author.id]
        current_warning = user_warnings[message.author.id]

        embed = discord.Embed(
            title="⚠️ Tindakan Diberikan",
            description=(f"{message.author.mention} telah di-timeout selama 60 menit karena melanggar aturan.\n"
                         f"Jumlah Peringatan: {current_warning}\n"
                         f"Jumlah Timeout: {current_timeout}"),
            color=discord.Color.orange()
        )
        await message.channel.send(embed=embed)

        user_warnings[message.author.id] = 0  # Reset peringatan

        if current_timeout >= timeout_limit:
            await ban_user(message)

    except Exception as e:
        embed = create_embed(
            title="Kesalahan Timeout",
            description=f"Terdapat masalah saat memberikan timeout: {e}"
        )
        await message.channel.send(embed=embed)

async def ban_user(message):
    try:
        await message.guild.ban(message.author, reason="Melebihi batas timeout")

        embed = discord.Embed(
            title="🚫 Pengguna Dilarang",
            description=(f"{message.author.mention} telah di-ban dari server karena sudah terkena timeout "
                         f"{timeout_limit} kali."),
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)

        # Reset data pengguna setelah ban
        if message.author.id in user_warnings:
            del user_warnings[message.author.id]
        if message.author.id in user_timeouts:
            del user_timeouts[message.author.id]

    except Exception as e:
        embed = create_embed(
            title="Kesalahan Ban",
            description=f"Terdapat masalah saat memberikan ban: {e}"
        )
        await message.channel.send(embed=embed)

async def send_warning(message, warning_count):
    timeout_count = user_timeouts[message.author.id]

    embed = discord.Embed(
        title="⚠️ Peringatan!",
        color=discord.Color.red()
    )
    embed.add_field(name="Jumlah Pelanggaran",
                    value=f"Peringatan: {warning_count}\nTimeout: {timeout_count}", inline=False)
    embed.add_field(name="⚠️ Harap Diperhatikan!",
                    value="Mengulangi pelanggaran dapat mengakibatkan timeout atau ban.", inline=False)
    embed.set_footer(text="Jaga sikap baik dan patuhi aturan!")

    await message.channel.send(embed=embed)

@bot.command()
async def blacklist(ctx):
    if blocked_words:
        embed = create_embed(
            title="Daftar Kata yang Diblokir",
            description="\n".join(blocked_words)
        )
        await ctx.send(embed=embed)
    else:
        embed = create_embed(
            title="Kata yang Diblokir",
            description="Tidak ada kata yang diblokir saat ini."
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def addblacklist(ctx, *, word: str = None):
    if word is None:
        embed = create_embed(
            title="Input Diperlukan",
            description="Tolong input kata-kata yang ingin di blacklist."
        )
        await ctx.send(embed=embed)
        return

    word = word.lower()
    if word not in blocked_words:
        blocked_words.append(word)
        embed = create_embed(
            title="Kata Ditambahkan",
            description=f"Kata '{word}' telah ditambahkan ke daftar blacklist."
        )
        await ctx.send(embed=embed)
    else:
        embed = create_embed(
            title="Kata Sudah Ada",
            description=f"Kata '{word}' sudah ada dalam daftar blacklist."
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        embed = create_embed(
            title="Pengguna Di-unban",
            description=f"{user.name} telah di-unban."
        )
        await ctx.send(embed=embed)
    except discord.NotFound:
        embed = create_embed(
            title="Pengguna Tidak Ditemukan",
            description="Pengguna tidak ditemukan atau tidak dibanned."
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(
            title="Izin Ditolak",
            description="Bot tidak memiliki izin untuk melakukan unban."
        )
        await ctx.send(embed=embed)
    except discord.HTTPException:
        embed = create_embed(
            title="Kesalahan Unban",
            description="Terjadi kesalahan saat mencoba unban pengguna."
        )
        await ctx.send(embed=embed)

bot.run('your token')

