package scanner_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/codethor0/ghost-sweep/internal/scanner"
)

func TestRunFindsGhostArtifacts(t *testing.T) {
	root := t.TempDir()

	if err := os.Mkdir(filepath.Join(root, "empty"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "empty.txt"), nil, 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("missing-target", filepath.Join(root, "broken-link")); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "real.txt"), []byte("ok"), 0o644); err != nil {
		t.Fatal(err)
	}

	findings, err := scanner.Run(root, scanner.DefaultScanners())
	if err != nil {
		t.Fatal(err)
	}

	kinds := map[scanner.Kind]int{}
	for _, f := range findings {
		kinds[f.Kind]++
	}

	if kinds[scanner.KindEmptyDir] != 1 {
		t.Fatalf("expected 1 empty_dir, got %d", kinds[scanner.KindEmptyDir])
	}
	if kinds[scanner.KindZeroByteFile] != 1 {
		t.Fatalf("expected 1 zero_byte_file, got %d", kinds[scanner.KindZeroByteFile])
	}
	if kinds[scanner.KindBrokenLink] != 1 {
		t.Fatalf("expected 1 broken_symlink, got %d", kinds[scanner.KindBrokenLink])
	}
}

func TestResolveRootRejectsFile(t *testing.T) {
	file := filepath.Join(t.TempDir(), "file.txt")
	if err := os.WriteFile(file, []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}

	if _, err := scanner.ResolveRoot(file); err == nil {
		t.Fatal("expected error for file path")
	}
}
