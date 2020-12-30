#include "arguments.h"
#include "registry.hpp"

#include <locale>
#include <codecvt>
#include <string>
#include <fstream>
#include <sphelper.h>

int wmain(int argc, wchar_t* argv[]) {
	// initialize COM
	if (FAILED(::CoInitialize(nullptr)))
		return -1;

	// initialize voice
	ISpVoice *pVoice = nullptr;
	if (FAILED(CoCreateInstance(CLSID_SpVoice, nullptr, CLSCTX_ALL, IID_ISpVoice, (void **)&pVoice))) {
		::CoUninitialize();
		return -1;
	}

	Arguments arguments = parseArguments(argc, argv);
	if (!arguments.inputFile || !arguments.outputFile || !arguments.voice) {
		pVoice->Release();
		::CoUninitialize();
		usage(argv[0]);
		return -2;
	}

	// pVoice->Speak requires wchar_t
	// https://stackoverflow.com/questions/4775437/read-unicode-utf-8-file-into-wstring

    const std::locale emptyLocale = std::locale::empty();
    typedef std::codecvt_utf8<wchar_t> converterType;
    const converterType* converter = new converterType;
    const std::locale utf8Locale = std::locale(emptyLocale, converter);
	std::wifstream stream(arguments.inputFile);
    stream.imbue(utf8Locale);
    std::wstring inputText;
    std::getline(stream, inputText);

	HRESULT hr;
	// set sample rate
	CSpStreamFormat	cAudioFmt(arguments.sampleRate, &hr);

	setVoice(pVoice, hr, arguments.voice);

	if (SUCCEEDED(hr)) {
		// set the output file
		ISpStream *pStream = nullptr;
		hr = SPBindToFile(arguments.outputFile, SPFM_CREATE_ALWAYS,
			&pStream, &cAudioFmt.FormatId(), cAudioFmt.WaveFormatExPtr());
		if (SUCCEEDED(hr)) {
			hr = pVoice->SetOutput(pStream, true);

		// output to file and free the pointers
			if (SUCCEEDED(hr))
				pVoice->Speak(inputText.c_str(), SPF_IS_XML, nullptr);
			pStream->Release();
		}
	}
    pVoice->Release();

	// uninitialize COM
	::CoUninitialize();

	return 0;
}
