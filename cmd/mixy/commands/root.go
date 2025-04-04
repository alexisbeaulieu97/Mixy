package commands

import (
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "mixy",
	Short: "Mixy creates project skeletons from templates.",
	Long:  `A flexible tool to generate projects by combining multiple templates (files, git repos, etc.) with variable substitution.`,
	// SilenceUsage is recommended for CLIs to avoid printing usage on expected errors.
	SilenceUsage: true,
}

// Execute adds all child commands to the root command and sets flags appropriately.
func Execute() error {
	return rootCmd.Execute()
}

func init() {
	// Add global flags here if needed later
}
