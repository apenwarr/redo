#include "main.h"
#include "libhello/hello.h"
#include "monotime.h"
#include "redoconf.h"
#include <stdio.h>

#if EXTRA_RC_INCLUDED != 1
#error "EXTRA_RC was not included!"
#endif

int main() {
	hello();
	printf("Timestamp: %s\n", stamp_time());
	printf("Monotime: %lld\n", monotime());
#ifdef CXX
	printf("Length of 'hello world': %d\n", cpp_test());
#else
	printf("No C++ compiler found.\n");
#endif
	flag_test();
	return 0;
}
