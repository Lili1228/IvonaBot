# ivona-bot
Bot do Discorda generujący syntezy mowy.

# Wymagania
* Python 3
* pip3 install -r requirements.txt
* ffmpeg
* serwer graficzny (bądź Windows) do instalacji SAPI5 bądź Ivony

Do obsługi SAPI5:
* wine
* winetricks

W repozytorium znajduje się demo IVONY Jacek na Linuxa, z osobną licencją w pliku bin/licencja_ivona_demo.txt, oraz bin/balcon.exe, składnik Balabolki, z poniższą licencją:

`You are free to use and distribute software for noncommercial purposes. For commercial use or distribution, you need to get permission from the copyright holder.`

# Instalacja
Poniższe polecenie instaluje SAPI5, wymagane do znakomitej większości wersji Ivony, wraz z trzema głosami Microsoftu (w tym Sam):

`winetricks speechsdk`

Teraz można zainstalować dowolną wersję IVONY (testowane na wersji rehabilitacyjnej).

# Konfiguracja

Na początku pliku znajduje się zmienna TOKEN, do której należy wpisać swój token do bota. Należy też utworzyć foldery, które są odpytywane przez funkcję `clean_cache()`.

# Użycie
`.ivona [tekst]`, `.ivona [plik tekstowy]` - wygenerowanie pliku Ivony i wysłanie na kanał

`.play ivona [tekst]`, `.play ivona [plik tekstowy]` - wygenerowanie pliku Ivony i odtworzenie na kanale głosowym

`.ivona demo`, `.play ivona demo` - j.w., ale dla wersji demonstracyjnej Ivony, znajdującej się w folderze bin

`.sam`, `.play sam` - j.w., ale dla Microsoft Sam
