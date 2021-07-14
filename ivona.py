import asyncio, hashlib, os
from pydub import AudioSegment

#Japanese to romaji
import cutlet, fugashi
katsu = cutlet.Cutlet()
katsu.use_foreign_spelling = False
katsu.ensure_ascii = False
#prevents from breaking really long words into parts
tagger = fugashi.Tagger('-M 512')
katsu.tagger = tagger

voices = ('sam', 'mary', 'mike', 'anna', 'lili', 'daniel', 'ivonademo', 'jacek', 'ewa', 'jennifer', 'carmen', 'eric', 'jan', 'maja', 'brian', 'amy', 'joey', 'kendra', 'kimberly', 'emma', 'chipmunk', 'hans', 'marlene', 'enrique', 'conchita', 'miguel', 'penelope', 'mathieu', 'celine', 'salli', 'ivy', 'gerainten', 'geraintcy', 'gwynethen', 'gwynethcy', 'nicole', 'agnieszka', 'giorgio', 'chantal', 'ricardo', 'vitoria', 'lotte', 'naja', 'karl', 'dora', 'russell', 'carla', 'ruben', 'mads', 'tatyana', 'astrid', 'cristiano', 'filiz', 'raveena', 'krzysztof', 'zosia', 'dave', 'steven', 'ludoviko')

async def create_tts(text, voice, filename) -> str:
	arg = ''
	if voice == 'ivonademo':
		arg = text.split(' ', 1)[0]
		if not arg.isnumeric() or int(arg) < 1 or int(arg) > 99:
			arg = '60'
		else:
			text = text.split(' ', 1)[1]
		f = open('/tmp/' + filename, 'wb')
		text = text.encode('cp1250', 'ignore')
	else:
		f = open('/tmp/' + filename, 'w')
	f.write(text)
	f.close()
	if voice in ('anna', 'lili'):
		arg = ' -16'
	if voice == 'ivonademo':
		os.system('bin/ivonacl -f /tmp/' + filename + ' -l bin/libvoice_pl_jl16demo.so --dur ' + arg + ' cache/ivonademo/' + filename + '.wav')
	else:
		os.system('bin/generate_sapi5.exe -i /tmp/' + filename + ' -n ' + voice + arg + ' -o cache/' + voice + '/' + filename + '.wav 2>/dev/null')
	os.remove('/tmp/' + filename)
	filename = 'cache/' + voice + '/' + filename
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

async def find_sound(text, voice):
	if voice == 'lili': #Lili is a Chinese voice and doesn't need conversion to Latin
		text = ' '.join(text.split())
	else:
		text = katsu.romaji(' '.join(text.split()))
	filename = hashlib.sha1(text.encode()).hexdigest()
	for ext in ('.wav', '.flac', '.ogg'):
		if os.path.exists('cache/' + voice + '/' + filename + ext):
			return text, filename, ext
	return text, filename, False

async def clean_cache() -> None:
	import time
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

