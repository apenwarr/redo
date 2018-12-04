# We don't normally build the cookbook examples, because they're
# not really part of redo itself.  But build them when testing,
# as a basic check that redo (and the examples) are valid.
redo cookbook/all
