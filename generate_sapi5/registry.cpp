#include "registry.hpp"
#include <locale>
#include <sphelper.h>

wchar_t **listVoices(ISpVoice *pVoice, HRESULT &hr, unsigned long &n) {
	wchar_t **ret = nullptr;
	ISpObjectToken *tok;
	hr = pVoice->GetVoice(&tok);
	if (SUCCEEDED(hr)) {
		ISpObjectTokenCategory *cat;
		hr = tok->GetCategory(&cat);
		if (SUCCEEDED(hr)) {
			IEnumSpObjectTokens *toks;
			hr = cat->EnumTokens(NULL, NULL, &toks);
			if (SUCCEEDED(hr)) {
				hr = toks->GetCount(&n);
				if (SUCCEEDED(hr)) {
					ret = new wchar_t*[n];
					for (unsigned long i = 0; i < n; ++i) {
						hr = toks->Item(i, &tok);
						if (FAILED(hr))
							break;
						ISpDataKey *key;
						hr = tok->OpenKey(L"Attributes", &key);
						if (FAILED(hr))
							break;
						hr = key->GetStringValue(L"Name", &(ret[i]));
						key->Release();
						if (FAILED(hr))
							break;
					}
				}
				toks->Release();
			}
			cat->Release();
		}
		tok->Release();
	}
	return ret;
}

void printVoices(ISpVoice *pVoice, HRESULT &hr) {
	unsigned long i, n;
	wchar_t **voices = listVoices(pVoice, hr, n);
	if (!voices)
		return;
	for (i = 0; i < n; ++i) {
		if (!voices[i])
			break;
		printf("%ls\n", voices[i]);
		delete[] voices[i];
	}
	delete[] voices;
}

void setVoice(ISpVoice *pVoice, HRESULT &hr, wchar_t *name) {
	unsigned long i, n;
	wchar_t **voices = listVoices(pVoice, hr, n);
	if (!voices)
		return;
	for (i = 0; i < wcslen(name); ++i)
		name[i] = std::tolower(name[i], std::locale());
	for (i = 0; i < n; ++i) {
		if (!voices[i])
			return;
		for (size_t j = 0; j < wcslen(voices[i]); ++j)
			voices[i][j] = std::tolower(voices[i][j], std::locale());
		if (wcsstr(voices[i], name)) {
			wchar_t *attribute = new wchar_t[6 + wcslen(voices[i])];
			wcscpy(attribute, L"Name=");
			wcscat(attribute, voices[i]);
			ISpObjectToken *cpToken;
			SpFindBestToken(SPCAT_VOICES, L"", attribute, &cpToken);
			pVoice->SetVoice(cpToken);
			cpToken->Release();
			delete[] attribute;
			break;
		}
	}
/*	for (i = 0; i < n; ++i)
		delete[] voices[i];*/

	delete[] voices;
}
