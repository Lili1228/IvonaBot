#!/usr/bin/env python3
# it's a Discord bot
import asyncio
import discord
import typing
from discord.ext import commands, tasks
# for clock in show_queue()
from datetime import datetime
# used for attachments to TTS and files to play
import magic
# for streaming music
import youtube_dl

# additional modules
from ivona import *

TOKEN = 'INSERT TOKEN HERE'
queue_size = 3

ytdl = youtube_dl.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True, 'default_search': 'auto',
                           'source_address': '0.0.0.0'})

bot = commands.Bot('.', help_command=None, strip_after_prefix=True, case_insensitive=True,
                   activity=discord.Activity(name='Najgorsze Gry Wszechczasów', type=discord.ActivityType.watching))
error_title = ':x: Error'

queue = {}

voices_diacritics = {'penélope': 'penelope', 'céline': 'celine', 'geraint': 'geraintcy', 'gwyneth': 'gwynethcy',
                     'vitória': 'vitoria', 'dóra': 'dora'}


async def add_to_queue(message, buf):
    if message.guild.id in queue.keys():
        if len(queue[message.guild.id]) == queue_size:
            await message.reply(
                embed=discord.Embed(title=error_title, description='The queue is full (' + str(queue_size) + ')!',
                                    color=0xff0000))
            if 'BytesIO' in str(type(buf)):
                buf.close()
            return
        else:
            queue[message.guild.id].append((message, buf))
            await message.reply(embed=discord.Embed(title=':white_check_mark: Added to queue!',
                                                    description='Sounds in queue: ' + str(
                                                        len(queue[message.guild.id])), color=0x008000))
            return
    else:
        # [] because deleting first element of a list
        queue[message.guild.id] = [(message, buf)]
        await message.reply(embed=discord.Embed(title=':white_check_mark: Added to queue!',
                                                description="It's the first sound in a queue.", color=0x008000))
        return


async def find_vc(channel):
    for i in bot.voice_clients:
        if i.channel == channel:
            return i
        elif i.guild.id == channel.guild.id:
            await i.move_to(channel)
            return i
    try:
        ret = await channel.connect()
        await channel.guild.change_voice_state(channel=channel, self_deaf=True)
        return ret
    except asyncio.TimeoutError:
        return None


async def play_sound(message, buf):
    if not message.author.voice:
        await message.channel.send(
            embed=discord.Embed(title=error_title, description="You aren't in a voice chat.", color=0xff0000),
            delete_after=10)
        if 'BytesIO' in str(type(buf)):
            buf.close()
        return
    vc = await find_vc(message.author.voice.channel)
    if not vc:
        await message.channel.send(
            embed=discord.Embed(title=error_title, description="Couldn't connect to voice chat.", color=0xff0000),
            delete_after=10)
        if 'BytesIO' in str(type(buf)):
            buf.close()
        return
    # issue 6385 of discord.py
    if 'BytesIO' in str(type(buf)):
        buf2 = buf
        filename = '/tmp/' + str(message.id)
        buf = open(filename, 'wb')
        buf2.seek(0)
        buf.write(buf2.getbuffer())
        buf.close()
        buf2.close()
        buf = filename
    try:
        vc.play(discord.FFmpegPCMAudio(buf, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'),
                after=lambda e: bot.loop.create_task(clean_vc(vc, buf)))
    except discord.ClientException:
        await add_to_queue(message, buf)


async def play_uploaded_sound(message):
    buf = BytesIO()
    await message.attachments[0].save(buf)
    filetype = magic.from_buffer(buf.read(2048), mime=True)
    if not (filetype.startswith('audio') or filetype.startswith('video')):
        await message.channel.send(
            embed=discord.Embed(title=error_title, description="The attachment is not a multimedia file.", color=0xff0000),
            delete_after=10)
        buf.close()
        return
    if filetype == 'audio/midi':
        filename = '/tmp/' + message.id + '.'
        f = open(filename + 'mid', 'wb')
        buf.seek(0)
        f.write(buf.read())
        buf.close()
        os.system('timidity ' + filename + 'mid -idqq -OwM -o ' + filename + 'bin')
        os.remove(filename + 'mid')
        buf = filename + 'bin'
    await play_sound(message, buf)


async def stream(message):
    text = message.content.split(' ', 1)[1]
    data = ytdl.extract_info(text, download=False)
    if 'entries' in data:
        data = data['entries'][0]
        embed = discord.Embed(title=data['title'], url=data['webpage_url'], color=0xff0000)
        embed.set_author(name=data['uploader'])
        embed.set_image(url=data['thumbnails'][-1]['url'].split('?')[0])
        await message.reply(embed=embed)
    await play_sound(message, data['url'])


@bot.command(None, aliases=['help', 'commands'])
async def bot_help(ctx):
    embed = discord.Embed(title=":scroll: List of commands", color=0x008080)
    embed.add_field(name='.help/.commands', value="You're reading this.", inline=False)
    embed.add_field(name='.(voice name)', value='Send a sound file of what you typed, '
                                                'either after a space or in attachment.')
    embed.add_field(name='.play (voice name)', value='Same as above, but play it on voice chat.')
    embed.add_field(name='.voices', value='List of voices to be used with above commands.')
    embed.add_field(name='.sapi', value='List of SAPI5 tags for advanced synthesis.', inline=False)
    embed.add_field(name = '.voices2', value="List of voices to be used with one of the SAPI5 tags.", inline=False)
    embed.add_field(name='.play', value='Play sound from attached file, URL or YouTube search query on voice chat.')
    embed.add_field(name='.queue', value="Check what's in voice chat queue.")
    embed.add_field(name='.next/.skip', value='Skip to the next sound in queue on voice chat.')
    embed.add_field(name='.remove (number)', value='Remove a sound of given number from voice chat queue.')
    embed.add_field(name='.stop', value='Stop all sounds on voice chat (bot exits automatically after 5 minutes).')
    await ctx.reply(embed=embed)


@bot.command(None, aliases=voices + list(voices_diacritics.keys()))
async def tts(message, voice=None, vc=None):
    # parsing text file
    if 'Context' in str(type(message)):
        voice = message.invoked_with.casefold()
        if voice not in voices:
            voice = voices_diacritics[voice]
        message = message.message
        vc = False
    if message.attachments:
        if message.attachments[0].size > 8192:
            await message.reply(embed=discord.Embed(title=error_title, description="Maximum file size is 8 KiB.",
                                                    color=0xff0000))
            return
        attachment = BytesIO()
        await message.attachments[0].save(attachment)
        if magic.from_buffer(attachment.read(), mime=True) != 'text/plain':
            await message.reply(embed=discord.Embed(title=error_title, description="The attachment is not a text file.",
                                                    color=0xff0000))
            return
        attachment.seek(0)
        iscp1250 = magic.from_buffer(attachment.read()).startswith('Non-ISO extended-ASCII text')
        attachment.seek(0)
        if iscp1250:
            text = attachment.read().decode('cp1250')
        else:
            text = attachment.read().decode()
        attachment.close()
    # parsing content
    else:
        try:
            text = message.content.split()
            if text[0].startswith('.'):
                if text[0] == '.':
                    del text[0]
                if vc:
                    del text[0]
                del text[0]
            text = ' '.join(text)
        except IndexError:
            return
    async with message.channel.typing():
        text, filename, ext = find_sound(text, voice)
        if not ext:
            ext = create_tts(text, voice, filename)
            if ext == 'empty':
                await message.channel.send(
                    embed=discord.Embed(title=error_title, description="Output file is empty.", color=0xff0000),
                    delete_after=10)
                return
    filename = 'cache/' + voice + '/' + filename + ext
    if vc:
        await message.channel.send('Done', delete_after=0)
        await play_sound(message, filename)
    else:
        try:
            await message.reply(file=discord.File(filename))
        except discord.Forbidden:
            return


@bot.command()
@commands.guild_only()
async def play(message, voice=None):
    message = message.message
    if voice in voices:
        await tts(message, voice, True)
        return
    if voice in voices_diacritics.keys():
        await tts(message, voices_diacritics[voice])
        return
    if message.attachments:
        await play_uploaded_sound(message)
    else:
        await stream(message)


@bot.command('voices')
async def list_voices(message):
    await message.reply(open('etc/voices.txt', 'r').read())


@bot.command('voices2')
async def list_voices(message):
    await message.reply(open('etc/voices2.txt', 'r').read())


@bot.command('sapi')
async def sapi_tags(ctx):
    embed = discord.Embed(title=":scroll: List of SAPI5 tags",
                          description='Except for <silence />, all the tags ending with /> can be also used on a '
                                      'block of text, for example `<volume level="50">volume 50</volume> volume '
                                      '100`\nFor DECtalk tags, check https://vt100.net/dec/ek-dtc03-om-001.pdf.',
                          color=0x008080)
    embed.add_field(name='<volume level="x" />', value="Set volume, from 0 to 100.", inline=False)
    embed.add_field(name='<rate absspeed="x" />',
                    value="Set absolute speed, from -10 to 10 (negatives are bugged with IVONA voice).")
    embed.add_field(name='<rate speed="x" />', value="Set relative speed to the current one.")
    embed.add_field(name='<silence msec="x"/>',
                    value="Insert a silence lasting x milliseconds (buggy with IVONA voice, dots can help).",
                    inline=False)
    embed.add_field(name='<pitch absmiddle="x" />', value="Set absolute pitch, from -10 to 10.")
    embed.add_field(name='<pitch middle="x" />', value="Set relative pitch to the current one.")
    embed.add_field(name='<pron sym="x" />',
                    value="Pronounce a phrase using sounds in sym argument separated by spaces. American "
                          "pronunciation is available at "
                          "https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms717239(v=vs.85)",
                    inline=False)
    embed.add_field(name='<partofsp part="x">y</partofsp>',
                    value="Treat `y` as a part of speech `x`, where `x` is one of these: Unknown, Noun, Verb, "
                          "Modifier, Function, Interjection", inline=False)
    embed.add_field(name='<context id="x">y</context>',
                    value="Treat `y` in a context `x`. More about contexts at "
                          "https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms723629(v=vs.85)",
                    inline=False)
    embed.add_field(name='<voice required="x=y,a=b" />',
                    value='Change voice according to `x` and `a` parameters with `y` and `b` values. These normally '
                          'include Name, Gender, Age and Language (locale IDs available at '
                          'https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/a29e5c28-9fb9-4c49'
                          '-8e43-4b9b8e733a05).', inline=False)
    embed.add_field(name='<voice optional="x=y,a=b" />',
                    value="Same as voice required, but if no voice with given parameters is available, some of them "
                          "can be ommited.", inline=False)
    embed.add_field(name='<lang langid="x" />', value='Same as <voice required="Language=x"/>', inline=False)
    await ctx.reply(embed=embed)


@bot.command('queue')
@commands.guild_only()
async def show_queue(ctx):
    if not ctx.author.voice:
        await ctx.channel.send(
            embed=discord.Embed(title=error_title, description="You aren't on voice chat.", color=0xff0000),
            delete_after=10)
        return

    desc = ''
    if ctx.guild.id not in queue:
        desc = 'Kolejka jest pusta.'
    else:
        for index, value in enumerate(queue[ctx.guild.id]):
            desc += str(index + 1) + '. ' + value[0].jump_url + '\n'
        desc += 'Wolnych slotów w kolejce: ' + str(queue_size - len(queue[ctx.guild.id]))

    time = datetime.now()
    timedisplay = time.strftime('%-I')
    if time.minute >= 30:
        timedisplay += '30'

    await ctx.reply(embed=discord.Embed(title=':clock' + timedisplay + ': Queue', description=desc, color=0x008080))


@bot.command(aliases=['next'])
@commands.guild_only()
async def skip(ctx):
    vc = await find_vc(ctx.author.voice.channel)
    if not vc:
        return
    vc.stop()


@bot.command('remove')
@commands.guild_only()
async def remove_from_queue(ctx, number: typing.Optional[int] = 1):
    if not ctx.author.voice:
        await ctx.channel.send(
            embed=discord.Embed(title=error_title, description="You aren't on voice chat.", color=0xff0000),
            delete_after=10)
        return

    if number > queue_size:
        await ctx.channel.send(embed=discord.Embed(title=error_title, color=0xff0000, delete_after=10,
                                                   description="The number you've given is larger than the "
                                                               'queue size (' + str(queue_size) + ').'))
        return
    if number > len(queue[ctx.guild.id]) or number < 1:
        await ctx.channel.send(embed=discord.Embed(title=error_title, delete_after=10,
                                                   description="There isn't an element in queue with index"
                                                       + str(len(queue[ctx.guild.id])) + '.', color=0xff0000))
        return
    del queue[ctx.guild.id][number - 1]
    await show_queue(ctx)


@bot.command()
@commands.guild_only()
async def stop(ctx):
    if ctx.guild.id in queue:
        for i in queue[ctx.guild.id]:
            if i[1].endswith('.bin'):
                os.remove(i[1])
    del queue[ctx.guild.id]
    await skip(ctx)


@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.id in blacklist:
        return

    if message.guild and not message.channel.permissions_for(message.guild.get_member(bot.user.id)).send_messages:
        return
    text = message.content.casefold()
    for voice in voices:
        if message.guild and message.channel.name == 'tts-' + voice:
            await tts(message, voice, True)
            return

    for pair in voices_diacritics.keys():
        if message.guild and message.channel.name == 'tts-' + pair:
            await tts(message, voices_diacritics[pair], True)
            return

    await bot.process_commands(message)


async def clean_vc(vc, buf):
    if 'str' in str(type(buf)):
        if buf.endswith('.bin'):
            os.remove(buf)
        """"
        else:
            buf.close()
        """
    if vc.guild.id in queue:
        pair = queue[vc.guild.id][0]
        if len(queue[vc.guild.id]) == 1:
            del queue[vc.guild.id]
        else:
            del queue[vc.guild.id][0]
        await play_sound(pair[0], pair[1])
        return

    for _ in range(600):
        if vc.is_playing():
            return
        await asyncio.sleep(.5)
    await vc.disconnect()


@bot.event
async def on_ready():
    text = 'Logged in as ' + bot.user.name + ' (' + str(bot.user.id) + ')'
    print(text)
    print('-' * len(text))
    oscce.start()


tasks.loop(hours=24)(clean_cache).start()
bot.run(TOKEN)
