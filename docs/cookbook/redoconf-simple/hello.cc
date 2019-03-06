#include "all.hpp"
#include "ssltest.h"

using namespace std;

int main() {
	cout << "Hello, world!"
	     << endl
	     << "libssl version " 
	     << hex << libssl_version()
	     << endl;
	return 0;
}
