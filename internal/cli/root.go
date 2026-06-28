package cli

import (
	"fmt"
	"os"

	"github.com/codethor0/ghost-sweep/internal/report"
	"github.com/codethor0/ghost-sweep/internal/scanner"
	"github.com/spf13/cobra"
)

var (
	scanPath   string
	jsonOutput bool
)

var rootCmd = &cobra.Command{
	Use:   "ghost-sweep",
	Short: "Find orphaned and stale filesystem artifacts",
	Long:  "ghost-sweep scans a directory tree for empty folders, broken symlinks, and zero-byte files.",
	RunE:  runScan,
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	rootCmd.Flags().StringVarP(&scanPath, "path", "p", ".", "Root directory to scan")
	rootCmd.Flags().BoolVar(&jsonOutput, "json", false, "Emit findings as JSON")
}

func runScan(cmd *cobra.Command, _ []string) error {
	root, err := scanner.ResolveRoot(scanPath)
	if err != nil {
		return err
	}

	findings, err := scanner.Run(root, scanner.DefaultScanners())
	if err != nil {
		return err
	}

	if jsonOutput {
		if err := report.WriteJSON(os.Stdout, findings); err != nil {
			return fmt.Errorf("write json: %w", err)
		}
		return nil
	}

	report.WriteText(os.Stdout, findings)
	return nil
}
