import json
KEY = json.load(open('config.json'))['key']
GUILD_ID = json.load(open('config.json'))['guild']
USER_ID = json.load(open('config.json'))['user']
GOOD_USER_ID = json.load(open('config.json'))['goodUser']
TEXT_CHANNEL = json.load(open('config.json'))['textChannel']

import discord, time

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

ourGuild = None
goodUser = None

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    global ourGuild, goodUser

    for guild in client.guilds:
        if guild.id == GUILD_ID:
            ourGuild = guild

    for member in ourGuild.members:
        if member.id == GOOD_USER_ID:
            goodUser = member

from mutagen.mp3 import MP3


audio = MP3("playme.mp3")
audio_length = audio.info.length
audioDiscord = discord.FFmpegPCMAudio("playme.mp3")

@client.event
async def on_voice_state_update(member, old, new):
    if member.id == USER_ID:
        if new.channel != goodUser.voice.channel:
            if old.channel == goodUser.voice.channel:
                for c in old.channel.guild.text_channels:
                    if c.id == TEXT_CHANNEL:
                        channel = c

                await channel.send("https://github.com/kubagp1/podkowa/image.gif", delete_after=audio_length*2)

                vcon = await old.channel.connect()

                vcon.play(audioDiscord)

                time.sleep(audio_length)
                await vcon.disconnect()

client.run(KEY)