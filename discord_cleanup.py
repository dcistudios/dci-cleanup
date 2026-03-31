import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import discord

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
INACTIVE_DAYS = int(os.getenv("INACTIVE_DAYS", "30"))

if not TOKEN:
    print("Error: DISCORD_TOKEN is not set in your .env file.")
    sys.exit(1)

# ── Helpers ───────────────────────────────────────────────────────────────────

DIVIDER = "─" * 44

def prompt_yes_no(question: str) -> bool:
    """Prompt the user with a y/n question. Accepts y/n/yes/no."""
    while True:
        answer = input(f"    {question} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter y or n.")

async def get_last_activity(
    guild: discord.Guild,
    user: discord.ClientUser,
    cutoff: datetime,
) -> datetime | None:
    """Return the most recent message time by `user` in `guild` after `cutoff`, or None."""
    for channel in guild.text_channels:
        try:
            async for message in channel.history(limit=50, after=cutoff):
                if message.author == user:
                    return message.created_at
        except (discord.Forbidden, discord.HTTPException):
            continue
    return None

async def set_status(client: discord.Client, text: str) -> None:
    """Silently update the client’s custom status."""
    try:
        await client.change_presence(activity=discord.CustomActivity(name=text))
    except Exception:
        pass

# ── Bot ───────────────────────────────────────────────────────────────────────

class CleanupBot(discord.Client):
    async def on_ready(self) -> None:
        print(f"\nLogged in as {self.user}")
        print(f"Scanning for servers inactive for >{INACTIVE_DAYS} days...\n")
        try:
            await self.run_cleanup()
        finally:
            await self.close()

    async def run_cleanup(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=INACTIVE_DAYS)
        guilds = list(self.guilds)
        total = len(guilds)
        inactive: list[discord.Guild] = []

        # ── Scan phase ────────────────────────────────────────────────────────
        for i, guild in enumerate(guilds, 1):
            print(f"[{i:>{len(str(total))}}/{total}] {guild.name}", end=" ", flush=True)
            await set_status(self, f"Scanning {i}/{total}")

            last_active = await get_last_activity(guild, self.user, cutoff)

            if last_active:
                print(f"→ active  ({last_active.strftime('%Y-%m-%d')})")
            else:
                print("→ INACTIVE")
                inactive.append(guild)

        await set_status(self, "scan complete")

        # ── Summary ───────────────────────────────────────────────────────────
        print(f"\n{DIVIDER}")
        print(f"  Scan complete — {len(inactive)} inactive / {total} total")
        print(DIVIDER)

        if not inactive:
            print("\n  Nothing to do. All servers are active!\n")
            return

        # ── Interactive leave phase ───────────────────────────────────────────
        print("\n  Choose which inactive servers to leave:\n")

        to_leave: list[discord.Guild] = []
        for idx, guild in enumerate(inactive, 1):
            members = f"{guild.member_count:,} members" if guild.member_count else "unknown size"
            print(f"  [{idx}/{len(inactive)}] {guild.name}  ({members})")
            if prompt_yes_no("Leave?"):
                to_leave.append(guild)
            print()

        if not to_leave:
            print("No servers selected. Nothing changed.")
            return

        # ── Leave phase ───────────────────────────────────────────────────────
        print(f"{DIVIDER}")
        print(f"  Leaving {len(to_leave)} server(s)...")
        print(DIVIDER + "\n")

        left, failed = 0, 0
        for guild in to_leave:
            try:
                await guild.leave()
                print(f"  ✓ Left:   {guild.name}")
                left += 1
                await asyncio.sleep(0.5)   # small delay to avoid rate limits
            except discord.HTTPException as e:
                print(f"  ✗ Failed: {guild.name}  ({e})")
                failed += 1

        print(f"\n  Done — left {left} server(s)" + (f", {failed} failed." if failed else "."))

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Standard intents are usually enough to see guilds, 
    # but you may need members intent if you want member_count accuracy.
    intents = discord.Intents.default()
    client = CleanupBot(intents=intents)
    client.run(TOKEN)
