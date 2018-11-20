read pid <../../pid

# Test that log retrieval works correctly when run from a different base dir.
redo-log -ru ../../x | grep -q "^$pid x stderr" || exit 45
redo-log -ru ../../x | grep -q "^$pid y stderr" || exit 46
