#!/usr/bin/env python3
import discord, asyncio, nacl, time, os
#tts imports
import hashlib, magic, random
from pydub import AudioSegment

TOKEN = 'INSERT TOKEN HERE'
client = discord.Client()

async def send_and_delete(channel, text, timeout=10):
	sending = await channel.send(text)
	await asyncio.sleep(timeout)
	await sending.delete()

async def find_vc(channel):
	for i in client.voice_clients:
		if i.channel == channel:
			return i
		elif i.guild.id == channel.guild.id:
			await i.move_to(channel)
			return i
	try:
		return await channel.connect()
	except asyncio.TimeoutError:
		return

def create_tts(text, voice, filename):
	if voice == 'Sam':
		f = open('/tmp/text.txt', 'w')
	else:
		f = open('/tmp/text.txt', 'w', encoding='cp1250')
	f.write(text)
	f.close()
	if voice == 'demo':
		os.system('bin/ivonacl -f /tmp/text.txt -l bin/libvoice_pl_jl16demo.so ' + filename + '.wav')
	else:
		os.system('wine bin/balcon -f /tmp/text.txt -n ' + voice + ' -w ' + filename + '.wav 2>/dev/null >/dev/null')
	if os.stat(filename + '.wav').st_size > 8*1024*1024:
		if os.stat(filename + '.wav').st_size > 12*1024*1024:
			AudioSegment.from_wav(filename + '.wav').export(filename + '.ogg', format = 'ogg')
			os.remove(filename + '.wav')
			return '.ogg'
		else:
			AudioSegment.from_wav(filename + '.wav').export(filename + '.flac', format = 'flac' )
			os.remove(filename + '.wav')
			return '.flac'
	else:
		return '.wav'

async def tts(message, voice, vc = False):
	if (len(message.content.split(' ')) > 1 and message.content.split(' ')[1].lower() == 'demo') or (vc and len(message.content.split(' ')) > 2 and message.content.split(' ')[2].lower() == 'demo'):
		voice = 'demo'
#parsing text file
	if message.attachments:
		if message.attachments[0].size > 8192:
			await message.channel.send('Maksymalny rozmiar pliku to 8 kB.')
			return
		await message.attachments[0].save('/tmp/text.txt')
		if magic.Magic(mime=True).from_file('/tmp/text.txt') != 'text/plain':
			await message.channel.send('To nie jest plik tekstowy.')
			return
		f = open('/tmp/text.txt', 'r')
		text = f.read()
		f.close()
#parsing content			
	else:
		text = message.content.split(' ', 1)[1]
		if vc:
			text = text.split(' ', 1)[1]
		if voice == 'demo':
			text = text.split(' ', 1)[1]
	found = False
	text = text.replace('…', '...')
	filename = 'cache/' + voice.split(' ')[0] + '/' + hashlib.sha1(text.encode()).hexdigest()
	async with message.channel.typing():
		for ext in {'.wav', '.flac', '.ogg'}:
			if os.path.exists(filename + ext):
				found = True
				filename = filename + ext
				break
		if not found:
			filename = filename + create_tts(text, voice, filename)
	if vc:
		if not message.author.voice:
			await send_and_delete(message.channel, 'Nie jesteś na czacie głosowym.')
			return
		channel = message.author.voice.channel
		found = False
		vc = await find_vc(message.author.voice.channel)
		if not vc:
			await send_and_delete(message.channel, 'Nie można połączyć z czatem głosowym.')
			return
		sending = await message.channel.send('Done')
		vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: client.loop.create_task(clean_vc(vc)))
		await sending.delete()
	else:
		await message.channel.send(file=discord.File(filename))

async def stop(message):
	vc = await find_vc(message.author.voice.channel)
	if not vc:
		return
	vc.stop()

@client.event
async def on_message(message):
	if message.author == client.user:
		return

	text = message.content.lower()
	if text.startswith('.play'):
		if text.startswith('.play ivona'):
			await tts(message, 'Ivona -fr 16', True)
		elif text.startswith('.play sam'):
			await tts(message, 'Sam', True)
		else:
			return
	elif text.startswith('.ivona'):
		await tts(message, 'Ivona -fr 16')
	elif text.startswith('.sam'):
		await tts(message, 'Sam')
	elif text == '.stop':
		await stop(message)

async def clean_cache():
	while(True):
		for folder in {'Ivona', 'demo', 'Sam'}:
			for audiofile in os.listdir('cache/' + folder):
				if (time.time() - os.path.getatime('cache/' + folder + '/' + audiofile) > 604800):
					os.remove(folder + '/' + audiofile)
		await asyncio.sleep(86400)

async def clean_vc(vc):
	for i in range(600):
		if vc.is_playing():
			return
		await asyncio.sleep(.5)
	await vc.disconnect()

@client.event
async def on_ready():
	await client.change_presence(activity=discord.Game("in the court"))
	print('Logged in as ' + client.user.name + ' (' + str(client.user.id) + ')')
	print('-----------------')

client.loop.create_task(clean_cache())
client.run(TOKEN)
