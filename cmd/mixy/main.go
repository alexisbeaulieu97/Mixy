package main

import (
	"fmt"
	"os"

	"github.com/alexisbeaulieu97/Mixy/cmd/mixy/commands" // Adjust path
)

func main() {
	if err := commands.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
