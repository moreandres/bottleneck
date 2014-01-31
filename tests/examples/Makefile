CC ?= gcc
CFLAGS ?= -Wall -Wextra -O3
PROGRAM ?= matrix

all:
	$(CC) $(CFLAGS) $(PROGRAM).c -o $(PROGRAM) -fopenmp

clean:
	rm -fr *~ $(PROGRAM) $(PROGRAM).o
