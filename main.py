import discord
from discord.ext import commands
import asyncio
import random
from discord.ext.commands import CommandNotFound
from ruamel.yaml import YAML

yaml = YAML()

with open("./config.yml", "r", encoding="utf-8") as file:
    config = yaml.load(file)

client = commands.Bot(command_prefix=config['prefix'], intents=discord.Intents.all(), case_insensitive=True)
client.remove_command('help')


@client.event
async def on_command_error(error):
    if isinstance(error, CommandNotFound):
        return
    raise error


@client.event
async def on_ready():
    print('------')
    print('Online! Details:')
    print(f"Bot Username: {client.user.name}")
    print(f"BotID: {client.user.id}")
    print('------')
    for command in client.commands:
        print(f"Loaded: {command}")
    configactivity = config['bot_activity']
    activity = discord.Game(name=config['bot_status_text'])
    await client.change_presence(status=configactivity, activity=activity)


def convert(time):
    pos = ["s", "m", "h", "d", "w"]
    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24, "w": 3600 * 24 * 7}
    unit = time[-1]

    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return -2

    return val * time_dict[unit]


@client.command()
@commands.has_role(config['giveaway_role'])
async def giveaway(ctx):

    timeout = config["setup_timeout"]
    embedq1 = discord.Embed(title=":tada: | SETUP ASSISTENT", description=f"Wilkommen beim einstellen des Giveaways, bitte beantworte folgende Fragen in ``{timeout}`` Sekunden!", color = ctx.author.color)
    embedq1.add_field(name=":star: | Frage 1", value="Wo soll das Giveaway sein?\n\n **Beispiel**: ``#General``")
    embedq2 = discord.Embed(title=":tada: | SETUP ASSISTENT", description="Großartig! Lass uns zur nächsten Frage gehen.", color = ctx.author.color)
    embedq2.add_field(name=":star: | Frage 2", value="Wie lange soll das Giveaway sein? ``<s|m|h|d|w>``\n\n **Beispiel**:\n ``1d``")
    embedq3 = discord.Embed(title=":tada: | SETUP ASSISTENT", description="Genial. Du hast es bis zur letzten Frage geschafft!", color = ctx.author.color)
    embedq3.add_field(name=":star: | Frage 3", value="Was soll man Geweinnen können?\n\n **Beispiel**:\n ``NITRO``")

    questions = [embedq1,
                 embedq2,
                 embedq3]

    answers = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for i in questions:
        await ctx.send(embed=i)

        try:
            msg = await client.wait_for('message', timeout=config['setup_timeout'], check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title=":tada: **Giveaway Assistent**", description=":x: Du warst zu langsam, bitte versuche es erneut", color = discord.Color.red())
            await ctx.send(embed=embed)
            return
        else:
            answers.append(msg.content)

    try:
        c_id = int(answers[0][2: -1])
    except:
        embed = discord.Embed(title=":tada: **Giveaway Assistent**", description=":x: Du hast denn Kanal nicht richtig angegeben!", color = discord.Color.red())
        await ctx.send(embed=embed)
        return

    channel = client.get_channel(c_id)

    time = convert(answers[1])
    if time == -1:
        embed = discord.Embed(title=":tada: **Giveaway Assistent**", description=":x: Du hast keine richtige Zeit einheit genutzt, hier hast du eine Liste:\n> s = Sekunden\n> m = Minuten\n> h = Stunden\n> d = Tage\n> w = Wochen!", color = discord.Color.red())
        await ctx.send(embed=embed)
        return
    elif time == -2:
        embed = discord.Embed(title=":tada: **Giveaway Assistent**", description=":x: Die Zeit **MUSS** eine ganze Zahl sein", color = discord.Color.red())
        await ctx.send(embed=embed)
        return
    prize = answers[2]

    embed = discord.Embed(title=":tada: **Giveaway Assistent**", description="Okay, alles war Richig. Das Gewinnspiel beginnt jetzt!", color = discord.Color.green())
    embed.add_field(name="Giveaway Chat:", value=f"{channel.mention}")
    embed.add_field(name="Zeit:", value=f"{answers[1]}")
    embed.add_field(name="Gewinn:", value=prize)
    await ctx.send(embed=embed)
    print(f"Neues Gewinnspiel gestartet von: {ctx.author.mention} | Gewinnspiel Chat: {channel.mention} | Zeit: {answers[1]} | Preis: {prize}")
    print("------")
    embed = discord.Embed(title=f":tada: **Gewinnspiel für: {prize}**", description=f"Reagiere mit {config['react_emoji']} zum Teilnehmen!", color=0x32cd32)
    embed.add_field(name="Zeit:", value=answers[1])
    embed.add_field(name=f"Gestartet von:", value=ctx.author.mention)
    msg = await channel.send(embed=embed)

    await msg.add_reaction(config['react_emoji'])
    await asyncio.sleep(time)

    new_msg = await channel.fetch_message(msg.id)
    users = await new_msg.reactions[0].users().flatten()
    users.pop(users.index(client.user))

    winner = random.choice(users)
    if config['ping_winner_message'] == True:
        await channel.send(f":tada: Herzlichen Glückwunsch! {winner.mention} du hast gewonnen, dein Preis: **{prize}**!")
        print(f"Neuer Gewinner! User: {winner.mention} | Preis: {prize}")
        print("------")

    embed2 = discord.Embed(title=f":tada: **Gewinnspiel für: {prize}**", description=f":trophy: **Gewinner:** {winner.mention}", color=0xffd700)
    embed2.set_footer(text="Gewinnspiel ist zu ende")
    await msg.edit(embed=embed2)


@client.command()
@commands.has_role(config['giveaway_role'])
async def reroll(ctx, channel: discord.TextChannel, id_: int):
    try:
        new_msg = await channel.fetch_message(id_)
    except:
        prefix = config['prefix']
        await ctx.send(f"Falsche Nutzung! Mach es so: `{prefix}reroll <Channel Name - Muss der Channel sein, wo das Giveaway war> <messageID von der Giveaway Nachricht>` ", color = discord.Color.red())

    users = await new_msg.reactions[0].users().flatten()
    users.pop(users.index(client.user))

    winner = random.choice(users)

    await ctx.channel.send(f":tada: Der neue Gewinner ist: {winner.mention}!")

@client.command()
async def time(ctx):
    if config['time_command'] == True:
        embed = discord.Embed(title="**Zeiten | :clock10:**", description=f"Alle Zeiten für das Giveaway\n\n> s = Sekunden (Seconds)\n> m = Minuten (Minutes)\n> h = Stunden (Hours)\n> d = Tage (Day)\n> w = Wochen (Week)", color = ctx.author.color)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.channel.send(embed=embed)
    else:
        return

@client.command()
async def help(ctx):
    if config['help_command'] == True:
        prefix = config['prefix']
        embed = discord.Embed(title="**Hilfe Seite | :book:**", description=f"Commands & Bot Settings. **Prefix**: ``{prefix}``", color = ctx.author.color)
        embed.add_field(name="Giveaway:", value=f"``{prefix}giveaway`` *Starte denn Giveaway Assistenten*", inline = False)
        embed.add_field(name="Reroll:", value=f"``{prefix}reroll <channel> <messageid>`` *Finde einen neuen Gewinner*", inline = False)
        embed.add_field(name="Time:", value=f"``{prefix}time`` *Zeigt dir alle Zeiten für das Giveaway an*", inline = False)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.channel.send(embed=embed)
    else:
        return


client.run(config['token'])
