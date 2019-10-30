umask 0022
redo mode1
MODE=$(../../redo/py -c \
	'import os; print(oct(os.stat("mode1").st_mode & 0o7777))')
[ "$MODE" = "0644" -o "$MODE" = "0o644" ] || exit 78
