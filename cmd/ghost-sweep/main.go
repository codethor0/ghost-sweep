package main

import (
	"os"

	"github.com/codethor0/ghost-sweep/internal/cli"
)

func main() {
	if err := cli.Execute(); err != nil {
		os.Exit(1)
	}
}
