exec >&2
rm -f want silent.out bork bork.log sub sub.log sub.warn

# Run a command without displaying its output.
# We are intentionally generating some redo errors, and
# we don't want the log to look scary.
# In case we need the output to debug a failed test,
# we leave the most recent command output in silent.out.
silent() {
	"$@" >silent.out 2>&1
}

# like "grep -q", but portable.
qgrep() {
	grep "$@" >/dev/null
}

# Returns true if bork is marked as a redo-source.
is_source() {
	redo-sources | qgrep '^bork$'
}

# Returns true if bork is marked as a redo-target.
is_target() {
	redo-targets | qgrep '^bork$'
}

# Returns true if bork is marked as an out-of-date redo-target.
is_ood() {
	redo-ood | qgrep '^bork$'
}

. ../skip-if-minimal-do.sh


# The table for our table-driven test.
# Column meanings are:
#   pre: the state of the 'bork' file at test start
#     src = 'bork' is a redo-source
#     nil = 'bork' is a redo-target that produced nil (ie. a virtual target)
#     add = 'bork' is a redo-target that produced a file
#   update: the override to perform after 'pre'
#     nop = do nothing
#     del = delete 'bork', if it exists
#     add = create/override a new 'bork'
#   post: the behaviour requested from bork.do after 'pre' and 'update' finish
#     err = bork.do exits with an error
#     nil = bork.do produces nil (ie. a virtual target)
#     add = bork.do produces a file
#   subran: 'ran' if sub.do is expected to pass, else 'skip'
#   ran: 'ran' if bork.do is expected to run at all, else 'skip'
#   warn: 'warn' if 'redo bork' is expected to warn about overrides, else 'no'
#   src/targ/ood: 1 if bork should show up in source/target/ood output, else 0
truth="
	# File was initially a source file
	src nop err   skip skip   no   1 0 0
	src nop nil   skip skip   no   1 0 0
	src nop add   skip skip   no   1 0 0

	src del err   skip ran    no   0 0 0   # content deleted
	src del nil   ran  ran    no   0 1 0
	src del add   ran  ran    no   0 1 0

	src add err   skip skip   no   1 0 0   # source updated
	src add nil   skip skip   no   1 0 0
	src add add   skip skip   no   1 0 0

	# File was initially a target that produced nil
	nil nop err   skip ran    no   0 0 0   # content forgotten
	nil nop nil   ran  ran    no   0 1 0
	nil nop add   ran  ran    no   0 1 0

	nil del err   skip ran    no   0 0 0   # content nonexistent
	nil del nil   ran  ran    no   0 1 0
	nil del add   ran  ran    no   0 1 0

	nil add err   skip skip   warn 1 0 0   # content overridden
	nil add nil   skip skip   warn 1 0 0
	nil add add   skip skip   warn 1 0 0

	# File was initially a target that produced output
	add nop err   skip ran    no   0 1 1   # update failed
	add nop nil   ran  ran    no   0 1 0
	add nop add   ran  ran    no   0 1 0

	add del err   skip ran    no   0 0 0   # content nonexistent
	add del nil   ran  ran    no   0 1 0
	add del add   ran  ran    no   0 1 0

	add add err   skip skip   warn 1 0 0   # content overridden
	add add nil   skip skip   warn 1 0 0
	add add add   skip skip   warn 1 0 0
"

echo "$truth" |
while read pre update post   subran ran   warn   src targ ood XX; do
	[ "$pre" != "" -a "$pre" != "#" ] || continue

	# add some helpful vertical whitespace between rows when
	# using 'redo -x'
	:
	:
	:
	:
	echo "test: $pre $update $post"
	rm -f bork

	# Step 1 does the requested 'pre' operation.
	: STEP 1
	../flush-cache
	case $pre in
	  src)
		# This is a little convoluted because we need to convince
		# redo to forget 'bork' may have previously been known as a
		# target.  To make it work, we have to let redo see the file
		# at least once as "should be existing, but doesn't."  That
		# will mark is as no longer a target.  Then we can create the
		# file from outside redo.
		rm -f bork
		echo err >want
		# Now redo will ack the nonexistent file, but *not* create
		# it, because bork.do will exit with an error.
		silent redo-ifchange bork || true
		# Make sure redo is really sure the file is not a target
		! is_target || exit 13
		# Manually create the source file and ensure redo knows it's
		# a source, and hasn't magically turned back into a target.
		echo src >>bork
		is_source || exit 11
		! is_target || exit 12
		;;
	  nil)
		echo nil >want
		redo bork
		! is_source || exit 11
		is_target || exit 12
		;;
	  add)
		echo add >want
		redo bork
		! is_source || exit 11
		is_target || exit 12
		;;
	  *) exit 90 ;;
	esac

	# Step 2 does the requested 'update' operation.
	: STEP 2
	skip=
	case $update in
	  nop) ;;
	  del) rm -f bork; skip=1 ;;
	  add) echo override >>bork ;;
	  *) exit 91 ;;
	esac

	../flush-cache
	if [ -z "$skip" ]; then
		silent redo sub
	fi

	# Step 3 does the requested 'post' operation.
	: STEP 3
	../flush-cache
	: >bork.log
	: >sub.log
	echo "$post" >want
	redo-ifchange sub >sub.warn 2>&1 || true

	read blog <bork.log || true
	case $ran in
	  skip) want_blog='' ;;
	  ran)  want_blog='x' ;;
	esac
	[ "$blog" = "$want_blog" ] || exit 21

	read slog <sub.log || true
	case $subran in
	  skip) want_slog='' ;;
	  ran)  want_slog='y' ;;
	esac
	[ "$slog" = "$want_slog" ] || exit 22

	if [ "$src" = 1 ]; then
		is_source || exit 31
	else
		! is_source || exit 32
	fi

	if [ "$targ" = 1 ]; then
		is_target || exit 33
	else
		! is_target || exit 34
	fi

	if [ "$ood" = 1 ]; then
		is_ood || exit 35
	else
		! is_ood || exit 36
	fi

	# FIXME: I'd like to not depend on the specific wording of warning
	# messages here.  However, the whole point of the warning message
	# is that it doesn't affect behaviour (or else it would be an error,
	# not a warning).
	if [ "$warn" = "warn" ]; then
		qgrep "you modified it" sub.warn || exit 51
	else
		! qgrep "you modified it" sub.warn || exit 52
	fi
done

exit 0
