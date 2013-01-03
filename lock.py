#!/usr/bin/env python

import sys, os, errno, glob, stat, lockfile, fcntl

class LockF(object):
    def __init__(self, name):
        self.name = name
        self.lock = lockfile.FileLock(name)
        self.owned = False
    
    def acquire(self, timeout=0):
        if vars.DEBUG_LOCKS: debug("%s (TRY LOCK %d)\n", self.name, timeout)
        try:
            res = self.lock.acquire(timeout)
        except:
            if vars.DEBUG_LOCKS: debug(" (FAILED)\n", self.name)
            raise
        else:
            if vars.DEBUG_LOCKS: debug(" (LOCKED)\n", self.name)
        self.owned = True
        return res
    
    def release(self):
        self.owned = False
        if vars.DEBUG_LOCKS: debug("%s (UNLOCK)\n", self.name)
        return self.lock.release()
    
    def is_locked(self):
        return self.lock.is_locked()
        
    def break_lock(self):
        self.owned = False
        if vars.DEBUG_LOCKS: debug("%s (BREAK)\n", self.name)
        return self.lock.break_lock()
    
    def __enter__(self):
        if vars.DEBUG_LOCKS: debug("%s (TRY LOCK)\n", self.name)
        try:
            res = self.lock.__enter__()
        except:
            if vars.DEBUG_LOCKS: debug("%s (FAILED)\n", self.name)
            raise
        else:
            if vars.DEBUG_LOCKS: debug("%s (LOCKED)\n", self.name)
        self.owned = True
        return res
    
    def __exit__(self, type, value, tb):
        self.owned = False
        if vars.DEBUG_LOCKS: debug("%s (UNLOCK)\n", self.name)
        return self.lock.__exit__(type, value, tb)

class ReadLock(object):
    def __init__(self, name):
        self.name = name
        self.lock = lockfile.FileLock(name + ".read")
        self.owned = False
    
    def acquire(self, timeout=0):
        self.lock.acquire(timeout)
        self.owned = True
    
    def release(self):
        self.owned = False
        self.lock.release()
    
    def is_locked(self):
        return self.lock.is_locked()
        
    def break_lock(self):
        self.owned = False
        self.lock.break_lock()
    
    def __enter__(self):
        self.lock.__enter__()
        self.owned = True
        return self
    
    def __exit__(self, type, value, tb):
        self.owned = False
        return self.lock.__exit__(type, value, tb)

class WriteLock(object):
    def __init__(self, name):
        self.name = name
        self.rlock = lockfile.FileLock(name + ".read")
        self.wlock = lockfile.FileLock(name + ".write")
        self.owned = False
    
    def acquire(self, timeout=0):
        self.rlock.acquire(timeout)
        self.wlock.acquire(timeout)
        self.owned = True
    
    def release(self):
        self.owned = False
        self.wlock.release()
        self.rlock.release()
    
    def is_locked(self):
        return self.wlock.is_locked()
        
    def break_lock(self):
        self.owned = False
        self.rlock.break_lock()
        self.wlock.break_lock()
    
    def __enter__(self):
        self.rlock.__enter__()
        self.wlock.__enter__()
        self.owned = True
        return self
    
    def __exit__(self, type, value, tb):
        self.owned = False
        x = self.wlock.__exit__(type, value, tb)
        y = self.rlock.__exit__(type, value, tb)
        return x or y
