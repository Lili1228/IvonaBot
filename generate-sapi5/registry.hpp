#ifndef _REGISTRY_HPP_
#define _REGISTRY_HPP_

#define _ATL_APARTMENT_THREADED
#include <atlbase.h>
extern CComModule _Module;
#include <atlcom.h>
#include <sapi.h>

/** Generates a list of available voices.
 @param [in] pVoice Pointer to the initialized voice.
 @param [in,out] hr Variable used to store command results.
 @param [out] n Size of returned array.
 @return Dynamic array of voice names.
 */
wchar_t **listVoices(ISpVoice *pVoice, HRESULT &hr, unsigned long &n);
/** Prints a list of voices, not used in program, left for debugging purposes.
 @see listVoices()
 @param [in] pVoice Pointer to the initialized voice, passed to listVoices().
 @param [in,out] hr Variable used to store command results, passed to listVoices().
 */
void printVoices(ISpVoice *pVoice, HRESULT &hr);
/** Changes a voice.
 @see listVoices()
 @param [in] pVoice Pointer to the initialized voice, passed to listVoices().
 @param [in,out] hr Variable used to store command results, passed to listVoices().
 @param [in] name Name of the voice to choose.
 */
void setVoice(ISpVoice *pVoice, HRESULT &hr, wchar_t *name);

#endif /* _REGISTRY_HPP_ */