#include "main.h"
#include <stdio.h>

#ifdef EXTRA_RC_INCLUDED
#error "rc/extra.rc should not be included when compiling flagtest.c"
#endif

void flag_test(void) {
	printf("flagtest included\n");
}
