CC ?= gcc
CFLAGS ?= -Wall -Wextra -O3

all: 
	$(CC) $(CFLAGS) heat2d.c -o heat2d -fopenmp
clean:
	rm -fr *~ heat2d heat2d.o
