package main

import (
	"errors"
	"fmt"
	"os"

	"github.com/alexisbeaulieu97/Mixy/cmd/mixy/commands" // Adjust path
	"github.com/alexisbeaulieu97/Mixy/internal/tui"
)

func main() {
	err := commands.Execute()
	if err != nil {
		// Check if the error is specifically user cancellation from the TUI
		if errors.Is(err, tui.ErrUserCancelled) {
			// Exit quietly without printing the full error stack for cancellation
			os.Exit(1) // Or os.Exit(0) if cancellation isn't considered an error state
		} else {
			// Print other errors normally
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}
	}
}
