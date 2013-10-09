CC ?= gcc
CFLAGS ?= -Wall -Wextra -O3

all: 
	$(CC) $(CFLAGS) matrix.c -o matrix -fopenmp
clean:
	rm -fr *~ matrix matrix.o
