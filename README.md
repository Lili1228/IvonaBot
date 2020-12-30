# IvonaBot
Bot do Discorda generujący syntezy mowy.

# Wymagania
* Python 3
* pip3 install -r requirements.txt
* ffmpeg
* serwer graficzny (bądź Windows) do instalacji SAPI5 bądź Ivony

Do obsługi SAPI5 na Linuxie:
* wine
* winetricks

Do obsługi plików midi:
* timidity

W repozytorium znajduje się demo IVONY Jacek na Linuxa, z osobną licencją w pliku bin/licencja_ivona_demo.txt, oraz bardzo prosty program w C++ do generowania plików dźwiękowych syntezy SAPI5, którego kod znajduje się w folderze generate_sapi5.

# Instalacja
Poniższe polecenie instaluje SAPI5, wymagane do znakomitej większości wersji Ivony, wraz z trzema głosami Microsoftu (w tym Sam):

`winetricks speechsdk`

Teraz można zainstalować dowolną wersję IVONY (bądź inne głosy).

# Konfiguracja

Na początku pliku znajduje się zmienna `TOKEN`, do której należy wpisać swój token do bota. Tuż pod nią znajduje się zmienna `queue_size`, która wyznacza rozmiar kolejki (domyślnie 3). Bot nie znajduje automatycznie głosów, należy je podać w zmiennej `voices`. Jeśli głos ma jakiś znak spoza ASCII, należy go dodać do zmiennej `voices_diacritics` w postaci (głos zapisany w ASCII, głos ze znakami spoza ASCII). Nazwy nie muszą być pełne.

# Użycie

`.help`, `.commands` - wyświetlenie listy komend

`.(nazwa głosu) [tekst]`, `.(nazwa głosu) [plik tekstowy]` - wygenerowanie pliku dźwiękowego z użyciem wskazanego głosu i wysłanie na kanał

`.play ivona [tekst]`, `.play ivona [plik tekstowy]` - wygenerowanie pliku dźwiękowego z użyciem wskazanego głosu i odtworzenie na kanale głosowym

`.voices` - wysłanie listy dostępnych głosów z pliku etc/voices.txt

`.sapi` - wysłanie listy tagów SAPI5

`.voices2` - wysłanie listy dostępnych głosów do tagu SAPI5 `<voice required="Name=nazwa głosu" />` z pliku etc/voices2.txt

`.play [plik multimedialny]` - odtworzenie załącznika na kanale głosowym

`.queue` - wysłanie aktualnej kolejki odtwarzanej na kanale głosowym

`.skip` - przejście do następnego dźwięku w kolejce na kanale głosowym

`.remove [liczba]` - usunięcie z kolejki na kanale głosowym dźwięku na podanej pozycji

`.stop` - wyzerowanie kolejki i zatrzymanie aktualnie odtwarzanego dźwięku na kanale głosowym

Bot automatycznie opuszcza kanał głosowy po 5 minutach.
