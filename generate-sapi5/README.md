# generate-sapi5

Bardzo prosty program w C++ do generowania SAPI5 do pliku tekstowego.

## Wymagania

Kompilowane przez Visual Studio 2010 Express (2010 wymagane z powodu użycia biblioteki codecvt) z Windows Server 2003 SP1 Platform SDK (w wersji Express brakuje nagłówka atlbase.h, jeśli masz płatną wersję VS2010, to prawdopodobnie nie będziesz tego potrzebować), oba dostępnie legalnie za darmo. Prawdopodobnie działa też z alternatywnymi kompilatorami Win32, nie użyto żadnych poleceń specyficznych dla Visual Studio.

## Użycie

    generate-sapi5.exe -i [input file] -o [output file] -n [voice name] [-16]

Gdzie:
	
`input file` to ścieżka do pliku tekstowego zapisanego jako UTF-8, który ma zostać wypowiedziany,

`output file` to ścieżka, gdzie będzie zapisany wynik syntezy,

`voice name` to nazwa (nie musi być pełna) głosu, który ma zostać użyty do syntezy,

`-16` ustawia częstotliwość pliku dźwiękowego na 16 kHz w celu zapobiegnięcia artefaktów w pierwszych wersjach IVONY.

Program zakłada, że w pliku tekstowym mogą znajdować się [tagi XML](https://docs.microsoft.com/en-us/previous-versions/windows/desktop/ms717077%28v=vs.85%29) i je poprawnie parsuje.
