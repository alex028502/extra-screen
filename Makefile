SHELL := /bin/bash
original=1280px-DEC_VT100_terminal_transparent.png

all: picture.png icon.png ctrl-space.bin
ctrl-space.bin: Makefile
	echo -ne '\x00' > $@
picture.png: $(original)
	convert $< -resize 96x96 $@
icon.png: $(original)
	convert $< -resize 48x48 $@
$(original): Makefile
	rm -f $@
	wget https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/DEC_VT100_terminal_transparent.png/$@
	touch $@
