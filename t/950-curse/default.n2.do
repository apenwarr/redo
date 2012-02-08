echo n2-$2
echo $2 >>$2.count
echo $2 >>in.countall

# we deliberately use 'redo' here instead of redo-ifchange, because this *heavily*
# stresses redo's locking when building in parallel.  We end up with 100
# different targets that all not only depend on this file, but absolutely must
# acquire the lock on this file, build it atomically, and release the lock.
redo countall
