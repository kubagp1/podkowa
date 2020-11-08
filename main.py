CONFIG_FILE_PATH = 'config.json'

import json
import discord
import mutagen.mp3
import time

class App():
    def __init__(self, confFilePath):

        # Config
        self.configFile = open(confFilePath)
        self.config = json.load(self.configFile)
        self.configFile.close()
        self.validateConfig(self.config)

        self.audio = discord.FFmpegPCMAudio("playme.mp3") # Preload to minimize latency
        # we need to reload discord for some reason nedds to reload this variable every time it plays

        audio = mutagen.mp3.MP3("playme.mp3")
        self.audioLength = audio.info.length

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
            ('goodUserId', int), 
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

        self.goodUser = None
        for guild in self.client.guilds:
            if self.goodUser: break
            for member in guild.members:
                if member.id == self.config['goodUserId']:
                    self.goodUser = member
                    break
        if not self.goodUser:
            raise Exception("Good user not found")
        else:
            print("Good user: {}".format(self.goodUser))

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
        new.channel != self.goodUser.voice.channel and \
        old.channel == self.goodUser.voice.channel:
            await self.badLeft(old.channel)
    
    async def on_message(self, message):
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

    async def badLeft(self, channel):
        await self.textChannel.send(self.config['message'], delete_after=self.audioLength*2)

        vcon = await channel.connect()
        vcon.play(self.audio)
        time.sleep(self.audioLength)
        await vcon.disconnect()

        self.audio = discord.FFmpegPCMAudio("playme.mp3") # Reload audio

if __name__ == "__main__":
    app = App(CONFIG_FILE_PATH)    