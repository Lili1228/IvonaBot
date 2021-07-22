#!/usr/bin/env python3
TOKEN = 'INSERT TOKEN HERE'
queue_size = 3

#it's a Discord bot
import asyncio, discord, typing
from discord.ext import commands, tasks
#for clock in show_queue()
import time
from datetime import datetime
#to remove unneeded files
import os
#used for attachments to TTS and files to play
import magic 
#so you don't have to save files on a disk
from io import BytesIO
#for streaming music
import youtube_dl
ytdl = youtube_dl.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True, 'default_search': 'auto', 'source_address': '0.0.0.0'})

from ivona import *

bot = commands.Bot('.', help_command = None, strip_after_prefix = True, case_insensitive = True, activity = discord.Activity(name = 'Najgorsze Gry Wszechczasów', type = discord.ActivityType.watching))
error_title = ':x: Błąd!'

queue={}

async def send_and_delete(channel, text = None, embed = None, timeout = 10):
	if channel.type == text and not channel.permissions_for(channel.guild.get_member(bot.user.id)).send_messages:
		return
	sending = await channel.send(text, embed = embed)
	if not sending:
		return
	await asyncio.sleep(timeout)
	await sending.delete()

async def add_to_queue(message, buf):
	if message.guild.id in queue.keys():
		if len(queue[message.guild.id]) == queue_size:
			await message.reply(embed = discord.Embed(title = error_title, description = 'Kolejka jest pełna (' + str(queue_size) + ')!', color = 0xff0000))
			if 'BytesIO' in str(type(buf)):
				buf.close()
			return
		else:
			queue[message.guild.id].append((message, buf))
			await message.reply(embed = discord.Embed(title = ':white_check_mark: Dodano do kolejki!', description = 'Dźwięków w kolejce: ' + str(len(queue[message.guild.id])), color = 0x008000))
			return
	else:
		# [] because deleting first element of a list
		queue[message.guild.id] = [(message, buf)]
		await message.reply(embed = discord.Embed(title = ':white_check_mark: Dodano do kolejki!', description = 'To pierwszy dźwięk w kolejce.', color = 0x008000))
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
		await channel.guild.change_voice_state(channel = channel, self_deaf = True)
		return ret
	except asyncio.TimeoutError:
		return

async def play_sound(message, buf):
	if not message.author.voice:
		await send_and_delete(message.channel, embed = discord.Embed(title = error_title, description = 'Nie jesteś na czacie głosowym.', color = 0xff0000))
		if 'BytesIO' in str(type(buf)):
			buf.close()
		return
	channel = message.author.voice.channel
	found = False
	vc = await find_vc(message.author.voice.channel)
	if not vc:
		await send_and_delete(message.channel, embed = discord.Embed(title = error_title, description = 'Nie można połączyć z czatem głosowym.', color = 0xff0000))
		if 'BytesIO' in str(type(buf)):
			buf.close()
		return
#issue 6385 of discord.py
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
		vc.play(discord.FFmpegPCMAudio(buf), after = lambda e: bot.loop.create_task(clean_vc(vc, buf)))
	except discord.ClientException:
		await add_to_queue(message, buf)

async def play_uploaded_sound(message):
	buf = BytesIO()
	await message.attachments[0].save(buf)
	type = magic.from_buffer(buf.read(2048), mime=True)
	if not type.startswith('audio') and not type.startswith('video'):
		await send_and_delete(message.channel, embed = discord.Embed(title = error_title, description = 'To nie jest plik multimedialny.', color = 0xff0000))
		buf.close()
		return
	if type == 'audio/midi':
		filename = '/tmp/' + message.id + '.'
		f = open(filename + 'mid', 'wb')
		buf.seek(0)
		f.write(buf.getbuffer())
		buf.close()
		os.system('timidity ' + filename + 'mid -idqq -OwM -o ' + filename + 'bin')
		os.remove(filename + 'mid')
		buf = filename + 'bin'
	await play_sound(message, buf)

async def stream(message):
	text = message.content.split(' ',1)[1]
	data = ytdl.extract_info(text, download = False)
	if 'entries' in data:
		data = data['entries'][0]
		embed = discord.Embed(title = data['title'], url = data['webpage_url'])
		embed.set_author(data['uploader'])
		embed.set_image(url=data['thumbnails'][-1]['url'].split('?')[0])
		await message.reply(embed = embed)
	await play_sound(message, data['url'])
	
@bot.command(aliases = ['commands'])
async def help(ctx):
	embed=discord.Embed(title = ":scroll: List of commands", color = 0x008080)
	embed.add_field(name = '.help/.commands', value = "You're reading this.", inline = False)
	embed.add_field(name = '.(voice name)', value = 'Send a sound file of what you typed, either after a space or in attachment.')
	embed.add_field(name = '.play (voice name)', value = 'Same as above, but play it on voice chat.')
	embed.add_field(name = '.voices', value = 'List of voices to be used with above commands.')
	embed.add_field(name = '.sapi', value = 'List of SAPI5 tags for advanced synthesis.', inline = False)
    embed.add_field(name = '.voices2', value="List of voices to be used with one of the SAPI5 tags.", inline=False)
	embed.add_field(name = '.play', value = 'Play sound from attached file, URL or YouTube search query on voice chat.')
	embed.add_field(name = '.queue', value = "Check what's in voice chat queue.")
	embed.add_field(name = '.next/.skip', value = 'Skip to the next sound in queue on voice chat.')
	embed.add_field(name = '.remove (number)', value = 'Remove a sound of given number from voice chat queue.')
	embed.add_field(name = '.stop', value = 'Stop all sounds on voice chat (bot exits automatically after 5 minutes).')
	await ctx.reply(embed=embed)

@bot.command(None, aliases = voices + list(voices_diacritics.keys()))
async def tts(message, voice = None, vc = None):
#parsing text file
	if 'Context' in str(type(message)):
		voice = message.invoked_with.casefold()
		if voice not in voices:
			voice = voices_diacritics[voice]
		message = message.message
		vc = False
	if message.attachments:
		if message.attachments[0].size > 8192:
			await message.reply(embed = discord.Embed(title = error_title, description = 'Maksymalny rozmiar pliku to 8 kB.', color = 0xff0000))
			return
		attachment = BytesIO()
		await message.attachments[0].save(attachment)
		if magic.from_buffer(attachment.read(), mime=True) != 'text/plain':
			await message.reply(embed=discord.Embed(title = error_title, description = 'To nie jest plik tekstowy.', color = 0xff0000))
			return
		attachment.seek(0)
		iscp1250 = magic.from_buffer(attachment.read()).startswith('Non-ISO extended-ASCII text')
		attachment.seek(0)
		if iscp1250:
			text = attachment.read().decode('cp1250')
		else:
			text = attachment.read().decode()
		attachment.close()
#parsing content			
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
				await send_and_delete(message.channel, embed = discord.Embed(title = error_title, description = 'Plik wynikowy jest pusty.', color = 0xff0000))
				return
	filename = 'cache/' + voice + '/' + filename + ext
	if vc:
		await send_and_delete(message.channel, 'Done', timeout=0)
		await play_sound(message, filename)
	else:
		try:
			await message.reply(file = discord.File(filename))
		except:
			return

@bot.command()
@commands.guild_only()
async def play(message, voice = None):
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
		stream(message)

@bot.command('voices')
async def list_voices(message):
	await message.reply(open('etc/voices.txt', 'r').read())

@bot.command()
async def voices2(message):
	await message.reply(open('etc/voices2.txt', 'r').read())

@bot.command('sapi')
async def sapi_tags(ctx):
	embed=discord.Embed(title = ":scroll: List of SAPI5 tags", description = 'Except for <silence />, all the tags ending with /> can be also used on a block of text, for example `<volume level="50">volume 50</volume> volume 100`.', color = 0x008080)
	embed.add_field(name = '<volume level="x" />', value = "Set volume, from 0 to 100.", inline = False)
	embed.add_field(name = '<rate absspeed="x" />', value = "Set absolute speed, from -10 to 10 (negatives are bugged with IVONA voice).")
	embed.add_field(name = '<rate speed="x" />', value = "Set relative speed to the current one.")
	embed.add_field(name = '<silence msec="x"/>', value = "Insert a silence lasting x milliseconds (buggy with IVONA voice, dots can help).", inline = False)
	embed.add_field(name = '<pitch absmiddle="x" />', value = "Set absolute pitch, from -10 to 10.")
	embed.add_field(name = '<pitch middle="x" />', value = "Set relative pitch to the current one.")
	embed.add_field(name = '<pron sym="x" />', value = "Pronounce a phrase using sounds in sym argument separated by spaces. American pronunciation is available at https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms717239(v=vs.85)", inline = False)
	embed.add_field(name = '<partofsp part="x">y</partofsp>', value = "Treat `y` as a part of speech `x`, where `x` is one of these: Unknown, Noun, Verb, Modifier, Function, Interjection", inline = False)
	embed.add_field(name = '<context id="x">y</context>', value = "Treat `y` in a context `x`. More about contexts at https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms723629(v=vs.85)", inline = False)
	embed.add_field(name = '<voice required="x=y,a=b" />', value = 'Change voice according to `x` and `a` parameters with `y` and `b` values. These normally include Name (for names, try .voices2), Gender, Age and Language (locale IDs available at https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/a29e5c28-9fb9-4c49-8e43-4b9b8e733a05).', inline = False)
	embed.add_field(name = '<voice optional="x=y,a=b" />', value = "Same as voice required, but if no voice with given parameters is available, some of them can be ommited.", inline = False)
	embed.add_field(name = '<lang langid="x" />', value = 'Same as <voice required="Language=x"/>', inline = False)
	await ctx.reply(embed = embed)

@bot.command('queue')
@commands.guild_only()
async def show_queue(ctx):
	if not ctx.author.voice:
		await send_and_delete(ctx.channel, embed = discord.Embed(title = error_title, description = 'Nie jesteś na czacie głosowym.', color = 0xff0000))
		return

	if not ctx.guild.id in queue:
		desc = 'Kolejka jest pusta.'
	else:
		for index, value in enumerate(queue[ctx.guild.id]):
			desc += str(i + 1) + '. ' + value[0].jump_url + '\n'
		desc += 'Wolnych slotów w kolejce: ' + str(queue_size - len(queue[ctx.guild.id]))

	time = datetime.now()
	timedisplay = time.strftime('%-I')
	if time.minute >= 30:
		timedisplay += '30'

	await ctx.reply(embed = discord.Embed(title = ':clock' + timedisplay + ': Kolejka', description = desc, color = 0x008080))

@bot.command(aliases=['next'])
@commands.guild_only()
async def skip(ctx, stop = False):
	try:
		vc = await find_vc(ctx.author.voice.channel)
	except:
		return
	vc.stop()

@bot.command('remove')
@commands.guild_only()
async def remove_from_queue(ctx, number: typing.Optional[int] = 1):
	if not ctx.author.voice:
		await send_and_delete(ctx.channel, embed = discord.Embed(title = error_title, description = 'Nie jesteś na czacie głosowym.', color = 0xff0000))
		return

	if number > queue_size:
		await send_and_delete(ctx.channel, embed = discord.Embed(title = error_title, description = 'Podany numer w kolejce jest większy niż rozmiar kolejki (' + str(queue_size) + ').', color = 0xff0000))
		return
	if number > len(queue[ctx.guild.id]) or number < 1:
		await send_and_delete(ctx.channel, embed = discord.Embed(title = error_title, description = 'Brak elementu w kolejce o numerze ' + str(len(queue[ctx.guild.id])) + '.', color = 0xff0000))
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
	if message.author == bot.user:
		return

	if message.guild and not message.channel.permissions_for(message.guild.get_member(bot.user.id)).send_messages:
		return
	text = message.content.casefold()

	for voice in voices:
		if (message.guild and message.channel.name == 'tts-' + voice):
			await tts(message, voice, True)
			return

	for pair in voices_diacritics.keys():
		if (message.guild and message.channel.name == 'tts-' + pair):
			await tts(message, voices_diacritics[pair], True)
			return

	await bot.process_commands(message)

async def clean_vc(vc, buf):
	if 'str' in str(type(buf)):
		try:
			if buf.endswith('.bin'):
				os.remove(buf)
		except:
			pass
#	else:
#		buf.close()
	if vc.guild.id in queue:
		pair = queue[vc.guild.id][0]
		if len(queue[vc.guild.id]) == 1:
			del queue[vc.guild.id]
		else:
			del queue[vc.guild.id][0]
		await play_sound(pair[0], pair[1])
		return

	for i in range(600):
		if vc.is_playing():
			return
		await asyncio.sleep(.5)
	await vc.disconnect()

@bot.event
async def on_ready():
	text = 'Logged in as ' + bot.user.name + ' (' + str(bot.user.id) + ')'
	print(text)
	print('-' * len(text))

tasks.loop(hours = 24)(clean_cache).start()
bot.run(TOKEN)
