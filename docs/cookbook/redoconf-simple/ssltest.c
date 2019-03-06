// An example of how to change code behaviour based on
// redoconf autodetection.
#include "redoconf.h"

#if HAVE_LIBSSL

#if HAVE_OPENSSL__SSL_H
#include <openssl/ssl.h>
#endif

#if HAVE_OPENSSL__OPENSSLV_H
#include <openssl/opensslv.h>
#endif

unsigned long libssl_version() {
	SSL_library_init();
	return OPENSSL_VERSION_NUMBER;
}

#else  // HAVE_LIBSSL

unsigned long libssl_version() {
	// Library not present
	return 0;
}

#endif // HAVE_LIBSSL

