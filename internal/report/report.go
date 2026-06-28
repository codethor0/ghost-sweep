package report

import (
	"encoding/json"
	"fmt"
	"io"
	"sort"

	"github.com/codethor0/ghost-sweep/internal/scanner"
)

func WriteJSON(w io.Writer, findings []scanner.Finding) error {
	sort.Slice(findings, func(i, j int) bool {
		if findings[i].Kind == findings[j].Kind {
			return findings[i].Path < findings[j].Path
		}
		return findings[i].Kind < findings[j].Kind
	})

	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	return enc.Encode(findings)
}

func WriteText(w io.Writer, findings []scanner.Finding) {
	sort.Slice(findings, func(i, j int) bool {
		if findings[i].Kind == findings[j].Kind {
			return findings[i].Path < findings[j].Path
		}
		return findings[i].Kind < findings[j].Kind
	})

	if len(findings) == 0 {
		fmt.Fprintln(w, "No ghost artifacts found.")
		return
	}

	counts := map[scanner.Kind]int{}
	for _, f := range findings {
		counts[f.Kind]++
	}

	fmt.Fprintf(w, "Found %d ghost artifact(s):\n", len(findings))
	for kind, count := range counts {
		fmt.Fprintf(w, "  %s: %d\n", kind, count)
	}
	fmt.Fprintln(w)

	for _, f := range findings {
		fmt.Fprintf(w, "[%s] %s\n", f.Kind, f.Path)
	}
}
