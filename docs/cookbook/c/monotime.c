#define __GNU_SOURCE
/*
 * Returns the kernel monotonic timestamp in microseconds.
 * This function never returns the value 0; it returns 1 instead, so that
 * 0 can be used as a magic value.
 */
#include "monotime.h"
#include "redoconf.h"

#if HAVE_CLOCK_GETTIME

#include <time.h>
#include <stdio.h>
#include <stdlib.h>

long long monotime(void) {
	struct timespec ts;
	if (clock_gettime(CLOCK_MONOTONIC, &ts) < 0) {
	  perror("clock_gettime");
	  exit(98); /* really should never happen, so don't try to recover */
	}
	long long result = ts.tv_sec * 1000000LL + ts.tv_nsec / 1000;
	return !result ? 1 : result;
}

#elif HAVE_MACH__MACH_TIME_H

#include <mach/mach.h>
#include <mach/mach_time.h>

long long monotime(void) {
	static mach_timebase_info_data_t timebase;
	if (!timebase.denom) mach_timebase_info(&timebase);
	long long result = (mach_absolute_time() * timebase.numer /
			   timebase.denom / 1000);
	return !result ? 1 : result;
}

#elif HAVE_WINDOWS_H

#include <windows.h>

/* WARNING: Not carefully tested. It might wrap around unexpectedly.
 * Based on suggestions from:
 * https://stackoverflow.com/questions/211257/windows-monotonic-clock
 */
long long monotime(void) {
	LARGE_INTEGER tps, t;
	QueryPerformanceFrequency(&tps); 
	QueryPerformanceCounter(&t);
	return t.QuadPart * 1000000LL / tps.QuadPart;
}

#else

#error "No monotonic time function is available"

#endif
