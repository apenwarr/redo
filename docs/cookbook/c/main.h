#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
#define CDEF extern "C"
#else
#define CDEF
#endif

/* when.c */
CDEF const char *stamp_time(void);

/* slow.cc */
CDEF int cpp_test(void);

/* flagtest.c */
CDEF void flag_test(void);

#endif /* __MAIN_H */