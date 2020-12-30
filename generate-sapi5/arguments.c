#include "arguments.h"

#include <stdio.h>
#include <string.h>

struct Arguments parseArguments(const int argc, wchar_t** argv) {
	struct Arguments ret = {NULL, NULL, NULL, SPSF_22kHz16BitMono};
	int i = 0;
	for (; i < argc; ++i)
		if (!wcscmp(argv[i], L"-16"))
			ret.sampleRate = SPSF_16kHz16BitMono;
		else if (i == argc - 1)
			break;
		else if (!wcscmp(argv[i], L"-i"))
			ret.inputFile = argv[++i];
		else if (!wcscmp(argv[i], L"-n"))
			ret.voice = argv[++i];
		else if (!wcscmp(argv[i], L"-o"))
			ret.outputFile = argv[++i];

	return ret;
}

void usage(const wchar_t *programName) {
	printf("Usage: %ls -i [input file] -n [voice name] -o [output file] [-16]\n", programName);
}
