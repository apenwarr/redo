#!/bin/sh

redo-ifchange \
 'double-quote-(\")' \
 'backslash-(\\)' \
 'alert-(\a)' \
 'backspace-(\b)' \
 'produce-no-further-output-(\c)' \
 'escape-(\e)' \
 'form-feed-(\f)' \
 'newline-(\n)' \
 'carriage-return-(\r)' \
 'horizontal-tab-(\t)' \
 'vertical-tab-(\v)' \
 'A-(\101)' \
 'A-(\x65)' \
 'ā-(\u0101)' \
 'ā-(\u00000101)' \
 'percent-(%%)'