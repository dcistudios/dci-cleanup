import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import discord

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
INACTIVE_DAYS = int(os.getenv("INACTIVE_DAYS", "30"))

class SelfBot(discord.Client):
    async def on_ready(self):
        print(f"\nLogged in as {self.user}\n")
        await self.check_inactive_servers()
        await self.close()

    async def check_inactive_servers(self):
        cutoff = datetime.now(timezone.utc) - timedelta(days=INACTIVE_DAYS)
        inactive = []
        guilds = list(self.guilds)
        total = len(guilds)

        print(f"Scanning {total} servers for inactivity (>{INACTIVE_DAYS} days)...\n")

        for i, guild in enumerate(guilds, 1):
            print(f"[{i}/{total}] Scanning: {guild.name}", flush=True)
            try:
                await self.change_presence(
                    activity=discord.CustomActivity(name=f"SCANNING {i}/{total}")
                )
            except Exception:
                pass

            last_message_time = None
            for channel in guild.text_channels:
                try:
                    async for message in channel.history(limit=50, after=cutoff):
                        if message.author == self.user:
                            last_message_time = message.created_at
                            break
                    if last_message_time:
                        break
                except (discord.Forbidden, discord.HTTPException):
                    continue

            if not last_message_time:
                print(f"  -> INACTIVE")
                inactive.append(guild)
            else:
                print(f"  -> Active (last message: {last_message_time.strftime('%Y-%m-%d')})")

        try:
            await self.change_presence(activity=discord.CustomActivity(name="scan complete"))
        except Exception:
            pass

        print(f"\nScan complete. {len(inactive)} inactive server(s) found.\n")

        if not inactive:
            print("Nothing to do!")
            return

        print("=" * 40)
        print("INACTIVE SERVERS - Choose which to leave:")
        print("=" * 40 + "\n")

        to_leave = []
        for idx, guild in enumerate(inactive, 1):
            print(f"[{idx}/{len(inactive)}] {guild.name} ({guild.member_count} members)")
            answer = input(f"    Would you like to leave? (y/n): ").strip().lower()
            print()
            if answer == "y":
                to_leave.append(guild)

        if not to_leave:
            print("No servers selected to leave.")
            return

        print(f"\nLeaving {len(to_leave)} server(s)...\n")
        for guild in to_leave:
            try:
                await guild.leave()
                print(f"  Left: {guild.name}")
            except discord.HTTPException as e:
                print(f"  Failed to leave {guild.name}: {e}")

        print("\nDone!")

client = SelfBot()
client.run(TOKEN)
