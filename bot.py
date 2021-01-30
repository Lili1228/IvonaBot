#!/usr/bin/env python3
import discord, asyncio, time, os
#tts imports
import hashlib, magic, random, tempfile
from datetime import datetime
from subprocess import Popen
#to convert wav to flac or ogg if the file is too big
from pydub import AudioSegment
#JP to romaji
import cutlet, fugashi

katsu = cutlet.Cutlet()
katsu.use_foreign_spelling = False
katsu.ensure_ascii = False
tagger = fugashi.Tagger('-M 512')
katsu.tagger = tagger

TOKEN = 'INSERT TOKEN HERE'
client = discord.Client()

error_title = ':x: Błąd!'
queue_size = 3

voices = ('sam', 'mary', 'mike', 'anna', 'lili', 'daniel', 'ivonademo', 'jacek', 'ewa', 'jennifer', 'carmen', 'eric', 'jan', 'maja', 'brian', 'amy', 'joey', 'kendra', 'kimberly', 'emma', 'chipmunk', 'hans', 'marlene', 'enrique', 'conchita', 'miguel', 'penelope', 'mathieu', 'celine', 'salli', 'ivy', 'geraint', 'gwyneth', 'nicole', 'agnieszka', 'giorgio', 'chantal', 'ricardo', 'vitoria', 'lotte', 'naja', 'karl', 'dora', 'russell', 'carla', 'ruben', 'mads', 'tatyana', 'astrid', 'cristiano', 'filiz', 'raveena')
voices_diacritics = {'penélope': 'penelope', 'céline': 'celine', 'dóra': 'dora'}

queue={}

async def help(message):
	embed=discord.Embed(title=":scroll: List of commands", color=0x008080)
	embed.add_field(name=".help/.commands", value="You're reading this.", inline=False)
	embed.add_field(name=".(voice name)", value="Send a sound file of what you typed, either after a space or in attachment.", inline=False)
	embed.add_field(name=".play (voice name)", value="Same as above, but play it on voice chat.")
	embed.add_field(name=".voices", value="List of voices to be used with above commands.", inline=False)
	embed.add_field(name=".sapi", value="List of SAPI5 tags for advanced synthesis.", inline=False)
	embed.add_field(name=".voices2", value="List of voices to be used with one of the SAPI5 tags.", inline=False)
	embed.add_field(name=".play + media attachment", value="Play sound from attached file on voice chat.", inline=False)
	embed.add_field(name=".queue", value="Check what's in voice chat queue.", inline=False)
	embed.add_field(name=".skip", value="Skip to the next sound in queue on voice chat.", inline=False)
	embed.add_field(name=".remove (number)", value="Remove a sound of given number from voice chat queue.", inline=False)
	embed.add_field(name=".stop", value="Stop all sounds on voice chat (bot exits automatically after 5 minutes).", inline=False)
	await message.reply(embed=embed)

async def send_and_delete(channel, text=None, embedded=None, timeout=10):
	if channel.type == text and not channel.permissions_for(channel.guild.get_member(client.user.id)).send_messages:
		return
	sending = await channel.send(text, embed=embedded)
	if not sending:
		return
	await asyncio.sleep(timeout)
	await sending.delete()

async def add_to_queue(message, filename, sending):
	if message.guild.id in queue.keys():
		if len(queue[message.guild.id]) == queue_size:
			await sending.edit(content=None, embed=discord.Embed(title=error_title, description='Kolejka jest pełna (' + str(queue_size) + ')!', color=0xff0000))
			return
		else:
			queue[message.guild.id].append([message, filename])
			await sending.edit(content=None, embed=discord.Embed(title=':white_check_mark: Dodano do kolejki!', description='Dźwięków w kolejce: ' + str(len(queue[message.guild.id])), color=0x008000))
			return
	else:
		queue[message.guild.id] = [[message, filename]]
		await sending.edit(content=None, embed=discord.Embed(title=':white_check_mark: Dodano do kolejki!', description='To pierwszy dźwięk w kolejce.', color=0x008000))
		return

async def show_queue(message):
	if not message.author.voice:
		await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='Nie jesteś na czacie głosowym.', color=0xff0000))
		return

	desc = ''

	if not message.guild.id in queue:
		desc='Kolejka jest pusta.'
	else:
		i = 1
		for j in queue[message.guild.id]:
			desc += str(i) + '. ' + j[0].jump_url + '\n'
			i += 1
		desc += 'Wolnych slotów w kolejce: ' + str(queue_size + 1 - i)

	time = datetime.now()
	timedisplay = time.strftime('%-I')
	if time.minute >= 30:
		timedisplay += '30'

	await message.reply(embed=discord.Embed(title=':clock' + timedisplay + ': Kolejka', description=desc, color=0x008080))

async def remove_from_queue(message):
	if not message.author.voice:
		await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='Nie jesteś na czacie głosowym.', color=0xff0000))
		return

	number = message.content.split(' ')[1]
	if not number or not number.isnumeric():
		await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='Nie podano numeru w kolejce do usunięcia.', color=0xff0000))
		return
	number = int(number)
	if number > queue_size:
		await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='Podany numer w kolejce jest większy niż rozmiar kolejki (' + str(queue_size) + ').', color=0xff0000))
		return
	if number > len(queue[message.guild.id]) or number < 1:
		await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='Brak elementu w kolejce o numerze ' + str(len(queue[message.guild.id])) + '.', color=0xff0000))
		return
	del queue[message.guild.id][number - 1]
	await show_queue(message)

async def find_vc(channel):
	for i in client.voice_clients:
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
		return

async def play_sound(message, filename):
	if not message.guild or not message.author.voice:
		await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='Nie jesteś na czacie głosowym.', color=0xff0000))
		return
	channel = message.author.voice.channel
	found = False
	vc = await find_vc(message.author.voice.channel)
	if not vc:
		await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='Nie można połączyć z czatem głosowym.', color=0xff0000))
		return
	sending = await message.reply('Done')
	try:
		vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: client.loop.create_task(clean_vc(vc, filename)))
		await sending.delete()
	except discord.ClientException:
		await add_to_queue(message, filename, sending)

async def play_uploaded_sound(message):
	filename = '/tmp/'
	for i in range(16):
		filename += chr(random.randrange(97, 97 + 26))
	filename += '.bin'
	await message.attachments[0].save(filename)
	type = magic.Magic(mime=True).from_file(filename)
	if not type.startswith('audio') and not type.startswith('video'):
		await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='To nie jest plik multimedialny.', color=0xff0000))
		return
	if type == 'audio/midi':
		os.rename(filename, '/tmp/temp.mid')
		os.system('timidity /tmp/temp.mid -idqq -OwM -o ' + filename)
	await play_sound(message, filename)

async def create_tts(text, voice, filename):
	arg = ''
	if voice == 'ivonademo':
		arg = text.split(' ', 1)[0] + ' '
		if not arg.isnumeric() or int(arg) < 1 or int(arg) > 99:
			arg = '60 '
		else:
			text = text.split(' ', 1)[1]
		f = open('/tmp/text.txt', 'wb')
		text = text.encode('cp1250', 'ignore')
	else:
		f = open('/tmp/text.txt', 'w')
	f.write(text)
	f.close()
	if voice in ('anna', 'lili'):
		arg = ' -16'
	if voice == 'ivonademo':
		os.system('bin/ivonacl -f /tmp/text.txt -l bin/libvoice_pl_jl16demo.so --dur ' + arg + filename + '.wav')
	else:
		os.system('bin/generate_sapi5.exe -i /tmp/text.txt -n ' + voice + arg + ' -o ' + filename + '.wav 2>/dev/null')
	if os.stat(filename + '.wav').st_size < 315:
		os.remove(filename + '.wav')
		return 'empty'
	if os.stat(filename + '.wav').st_size > 8*1024*1024:
		if os.stat(filename + '.wav').st_size > 12*1024*1024:
			AudioSegment.from_wav(filename + '.wav').export(filename + '.ogg', format = 'ogg')
			os.remove(filename + '.wav')
			return '.ogg'
		else:
			AudioSegment.from_wav(filename + '.wav').export(filename + '.flac', format = 'flac')
			os.remove(filename + '.wav')
			return '.flac'
	return '.wav'

async def sapi_tags(message):
	embed=discord.Embed(title=":scroll: List of SAPI5 tags", description='Except for <silence />, all the tags ending with /> can be also used on a block of text, for example `<volume level="50">volume 50</volume> volume 100`.', color=0x008080)
	embed.add_field(name='<volume level="x" />', value="Set volume, from 0 to 100.", inline=False)
	embed.add_field(name='<rate absspeed="x" />', value="Set absolute speed, from -10 to 10.", inline=False)
	embed.add_field(name='<rate speed="x" />', value="Set relative speed to the current one.")
	embed.add_field(name='<pitch absmiddle="x" />', value="Set absolute pitch, from -10 to 10.", inline=False)
	embed.add_field(name='<pitch middle="x" />', value="Set relative pitch to the current one.")
	embed.add_field(name='<silence msec="x"/>', value="Insert a silence lasting x milliseconds.", inline=False)
	embed.add_field(name='<pron sym="x" />', value="Pronounce a phrase using sounds in sym argument separated by spaces. American pronunciation is available at https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms717239(v=vs.85)", inline=False)
	embed.add_field(name='<partofsp part="x">y</partofsp>', value="Treat `y` as a part of speech `x`, where `x` is one of these: Unknown, Noun, Verb, Modifier, Function, Interjection", inline=False)
	embed.add_field(name='<context id="x">y</context>', value="Treat `y` in a context `x`. More about contexts at https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms723629(v=vs.85)", inline=False)
	embed.add_field(name='<voice required="x=y,a=b" />', value='Change voice according to `x` and `a` parameters with `y` and `b` values. These include Name (for names, try .voices2), Gender, Age and Language (locale IDs available at https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/a29e5c28-9fb9-4c49-8e43-4b9b8e733a05).', inline=False)
	embed.add_field(name='<voice optional="x=y,a=b" />', value="Same as voice required, but if no voice with given parameters is available, some of them can be ommited.", inline=False)
	embed.add_field(name='<lang langid="x" />', value='Same as <voice required="Language=x"/>', inline=False)
	await message.reply(embed=embed)

async def tts(message, voice, vc = False):
#parsing text file
	if message.attachments:
		if message.attachments[0].size > 8192:
			await message.reply(embed=discord.Embed(title=error_title, description='Maksymalny rozmiar pliku to 8 kB.', color=0xff0000))
			return
		await message.attachments[0].save('/tmp/text.txt')
		if magic.Magic(mime=True).from_file('/tmp/text.txt') != 'text/plain':
			await message.reply(embed=discord.Embed(title=error_title, description='To nie jest plik tekstowy.', color=0xff0000))
			return
		if magic.Magic().from_file('/tmp/text.txt').startswith('Non-ISO extended-ASCII text,'):
			f = open('/tmp/text.txt', 'r', encoding='cp1250')
		else:
			f = open('/tmp/text.txt', 'r')
		text = f.read()
		f.close()
#parsing content			
	else:
		if vc:
			text = message.content.split(' ', 2)[2]
		else:
			text = message.content.split(' ', 1)[1]
	found = False
	if voice == 'lili':
		text = ' '.join(text.split())
	else:
		text = katsu.romaji(' '.join(text.split()))
	filename = 'cache/' + voice + '/' + hashlib.sha1(text.encode()).hexdigest()
	async with message.channel.typing():
		for ext in ('.wav', '.flac', '.ogg'):
			if os.path.exists(filename + ext):
				found = True
				filename = filename + ext
				break
		if not found:
			filename = filename + await create_tts(text, voice, filename)
			if filename.endswith('empty'):
				await send_and_delete(message.channel, embedded=discord.Embed(title=error_title, description='Plik wynikowy jest pusty.', color=0xff0000))
				return
	if vc:
		await play_sound(message, filename)
	else:
		try:
			await message.reply(file=discord.File(filename))
		except:
			return

async def skip(message, stop=False):
	vc = await find_vc(message.author.voice.channel)
	if not vc:
		return
	if stop and message.guild.id in queue:
		for i in queue[message.guild.id]:
			if i[1].endswith('.bin'):
				os.remove(i[1])
		del queue[message.guild.id]
	vc.stop()

@client.event
async def on_message(message):
	if message.author == client.user:
		return

	if message.guild and not message.channel.permissions_for(message.guild.get_member(client.user.id)).send_messages:
		return
	text = message.content.casefold()
	for voice in voices:
		if text.startswith('.play ' + voice):
			await tts(message, voice, True)
			return
		elif text.startswith('.' + voice):
			await tts(message, voice)
			return
	for pair in voices_diacritics.keys():
		if text.startswith('.play ' + pair):
			await tts(message, voices_diacritics[pair], True)
			return
		elif text.startswith('.' + pair):
			await tts(message, voices_diacritics[pair])
			return

	if text == '.play' and message.attachments:
		await play_uploaded_sound(message)
	elif text == '.skip':
		await skip(message)
	elif text.startswith('.remove'):
		await remove_from_queue(message)
	elif text == '.stop':
		await skip(message, True)
	elif text == '.voices':
		await message.reply(open('etc/voices.txt', 'r').read())
	elif text == '.queue':
		await show_queue(message)
	elif text.startswith('.sapi'):
		await sapi_tags(message)
	elif text == '.help' or text == '.commands':
		await help(message)

async def clean_cache():
	while(True):
		if not os.path.isdir('cache'):
			if os.path.isfile('cache'):
				os.remove('cache')
			os.mkdir('cache', 0o700)
		for folder in voices:
			if not os.path.isdir('cache/' + folder):
				if os.path.isfile('cache/' + folder):
					os.remove('cache/' + folder)
				os.mkdir('cache/' + folder, 0o700)
				continue
			for audiofile in os.listdir('cache/' + folder):
				if (time.time() - os.path.getatime('cache/' + folder + '/' + audiofile) > 604800):
					os.remove('cache/' + folder + '/' + audiofile)
		await asyncio.sleep(86400)

async def clean_vc(vc, filename):
	if filename.endswith('.bin'):
		os.remove(filename)
	if vc.guild.id in queue.keys():
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

@client.event
async def on_ready():
	await client.change_presence(activity=discord.Activity(name='Najgorsze Gry Wszechczasów', type=discord.ActivityType.watching))
	text = 'Logged in as ' + client.user.name + ' (' + str(client.user.id) + ')'
	print(text)
	print('-' * len(text))

client.loop.create_task(clean_cache())
client.run(TOKEN)
