#ifndef _ARGUMENTS_H_
#define _ARGUMENTS_H_

#ifdef __cplusplus
extern "C" {
#endif

#include <sapi.h>

/// Structure used to parse arguments.
struct Arguments {
	/// Path to the input file.
	wchar_t *inputFile;
	/// Name of the voice.
	wchar_t *voice;
	/// Path to the output file.
	wchar_t *outputFile;
	/// Sample rate of generated sound file, set to SPSF_22kHz16BitMono by default.
	SPSTREAMFORMAT sampleRate;
};

/** Parses the arguments taken from command line arguments.
 @param [in] argc Number of arguments.
 @param [out] argv Array of arguments.
 @return A structure of parsed arguments.
 */
struct Arguments parseArguments(const int argc, wchar_t** argv);

/** Prints available program arguments.
 @param [in] Name of the invoked program binary.
 */
void usage(const wchar_t *programName);

#ifdef __cplusplus
}
#endif

#endif /* _ARGUMENTS_H_ */
