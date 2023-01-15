#include <stdio.h>
#include <stdlib.h>

#define N 10

int main() {
	FILE *out = fopen("output.dat", "w");
	int i;

	for(i = 0; i < N; i++) {
		fprintf(out, "%d %.3lf\n", i, i / (double) 100);
		fprintf(stdout, "%d\n", i);
	}
	fprintf(stderr, "Some debug info that shouldn't be here...\n");

//	fclose(out); // commented to work up valgrind

	return 0;
}
