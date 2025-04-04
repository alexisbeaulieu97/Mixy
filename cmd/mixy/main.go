// cmd/mixy/main.go
package main

import (
	"errors"
	"fmt"
	"os"

	"github.com/alexisbeaulieu97/Mixy/cmd/mixy/commands"
	"github.com/alexisbeaulieu97/Mixy/internal/core" // Need core for ErrCancelled check
)

func main() {
	// commands.Execute() handles cobra errors internally now using RunE
	err := commands.Execute()
	if err != nil {
		// Check if it was cancellation, which might have already printed a message
		if errors.Is(err, core.ErrCancelled) {
			// Potentially exit with a different code for cancellation?
			os.Exit(1) // Exit non-zero for cancellation
		} else {
			// Print the user-facing error returned by RunE
			// Logging should have happened within the command execution
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}
	}
	// Successful execution
	os.Exit(0)
}
