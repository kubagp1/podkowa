CONFIG_FILE_PATH = 'config.json'

import json
import discord
import mutagen.mp3
import time
import sqlite3
import ctypes
import ctypes.util
import random

class App():
    def __init__(self, confFilePath):

        # Config
        self.configFile = open(confFilePath)
        self.config = json.load(self.configFile)
        self.configFile.close()
        self.validateConfig(self.config)

        self.audio = discord.FFmpegPCMAudio("playme.mp3") # Preload to minimize latency
        # we need to reload bcs discord for some reason needs to reload this variable every time it plays
        
        print("ctypes - Find opus:")
        a = ctypes.util.find_library('opus')
        print(a)
        
        print("Discord - Load Opus:")
        b = discord.opus.load_opus(a)
        print(b)
        
        print("Discord - Is loaded:")
        c = discord.opus.is_loaded()
        print(c)

        audio = mutagen.mp3.MP3("playme.mp3")
        self.audioLength = audio.info.length

        # Set up sqlite for swearcounter

        self.db = sqlite3.connect('db.sqlite')
        self.c = self.db.cursor()

        self.c.execute('''
            CREATE TABLE IF NOT EXISTS swearsCount (
                id integer PRIMARY KEY,
                swears interger NOT NULL
            );
        ''')

        self.db.commit()

        # Set up client
        intents = discord.Intents.default()
        intents.members = True

        self.client = discord.Client(intents=intents)

        self.client.event(self.on_voice_state_update)
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

        self.client.run(self.config['key'])

    @staticmethod
    def validateConfig(c):
        # Convert dict to list with only key names and to list with only values
        names = []
        values = []
        configs = []
        for conf in c.items():
            names.append(conf[0])
            values.append(conf[1])
            configs.append(conf)


        valids = [('key', str),
            ('badUserId', int), 
            ('message', str), 
            ('goodUsersIds', list), 
            ('textChannelId', int)] # Valid config names and types

        validNames = []
        for valid in valids:
            validNames.append(valid[0]) # Extract just names from v

        for validName in validNames:
            if validName not in names:
                raise Exception('There is "{}" missing in config file'.format(validName))

        for config in configs:
            if config[0] not in validNames:
                continue
            else:
                index = validNames.index(config[0])

                if type(config[1]) != valids[index][1]:
                    raise Exception('Type of "{}" in config is {} and not {}'.format(
                        names[index], 
                        type(config[1]).__name__, 
                        valids[index][1].__name__))

    async def on_ready(self):
        print('We have logged in as {0.user}'.format(self.client))

        # self.goodUser = None
        # for guild in self.client.guilds:
        #     if self.goodUser: break
        #     for member in guild.members:
        #         if member.id == self.config['goodUserId']:
        #             self.goodUser = member
        #             break
        # if not self.goodUser:
        #     raise Exception("Good user not found")
        # else:
        #     print("Good user: {}".format(self.goodUser))

        self.textChannel = None
        for guild in self.client.guilds:
            if self.textChannel: break
            for textChannel in guild.text_channels:
                if textChannel.id == self.config['textChannelId']:
                    self.textChannel = textChannel
                    break
        if not self.textChannel:
            raise Exception("Text channel not found")
        else:
            print("Text channel: {}".format(self.textChannel))

    async def on_voice_state_update(self, member, old, new):
        if member.id == self.config['badUserId'] and \
        new.channel != old.channel:
            for oldMember in old.channel.members:
                if oldMember.id in self.config['goodUsersIds']:
                    await self.badLeft(old.channel)
                    break
    
    async def on_message(self, message):
        if message.author.id == 249836758009643008 and random.randrange(0,100)<60:
            await message.delete()

        if message.content.lower() == "podkowa trigger":
            if message.author.id == self.config['badUserId']:
                await message.channel.send("Nie dla psa")
                return
            elif not message.author.voice:
                await message.channel.send("Nie ma cie na vc debilu -_-")
                return
            else:
                await message.channel.send("Ok szefie")
                await self.badLeft(message.author.voice.channel)
        
        elif message.content.startswith('#s'):
            if message.mentions:
                for mention in message.mentions:
                    await message.channel.send('{} ma zrobić {} pompek/ki/kę'.format(mention.display_name, self.getSwears(mention.id)))
            else:
                    await message.channel.send('{} ma zrobić {} pompek/ki/kę'.format(message.author.display_name, self.getSwears(message.author.id)))
            await message.delete()

        elif message.content.startswith('#0'):
            if message.mentions:
                for mention in message.mentions:
                    self.resetSwears(mention.id)
            else:
                self.resetSwears(message.author.id)
            await message.delete()

        elif message.content.startswith("#"):
            t = message.content.split()
            if message.mentions:
                for mention in message.mentions:
                    if len(t) == 2:
                        self.addSwear(mention.id, 1)
                    elif len(t) == 3:
                        self.addSwear(mention.id, int(t[2]))
            elif len(t) == 2:
                self.addSwear(message.author.id, int(t[1]))

            await message.delete()

    async def badLeft(self, channel):
        await self.textChannel.send(self.config['message'], delete_after=self.audioLength*2)

        vcon = await channel.connect()
        vcon.play(self.audio)
        time.sleep(self.audioLength)
        await vcon.disconnect()

        self.audio = discord.FFmpegPCMAudio("playme.mp3") # Reload audio

    def addSwear(self, memberId, s):
        if self.c.execute('SELECT COUNT(*) FROM swearsCount WHERE id = {}'.format(memberId)).fetchone()[0] == 1: # If there is member in db
            self.c.execute('UPDATE swearsCount SET swears = {} WHERE id = {}'.format(
                self.c.execute('SELECT swears FROM swearsCount WHERE id = {}'.format(memberId)).fetchone()[0]+s, 
                memberId)
            )
        else: # If there is not yet 
            self.c.execute('INSERT INTO swearsCount VALUES ({}, {})'.format(memberId, s))
        self.db.commit()

    def getSwears(self, memberId):
        return self.c.execute('SELECT swears FROM swearsCount WHERE id = {}'.format(memberId)).fetchone()[0]
    
    def resetSwears(self, memberId):
        self.c.execute('UPDATE swearsCount SET swears = 0 WHERE id = {}'.format(memberId))
        self.db.commit()

if __name__ == "__main__":
    app = App(CONFIG_FILE_PATH)    