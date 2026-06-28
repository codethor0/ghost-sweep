package scanner

import (
	"fmt"
	"os"
	"path/filepath"
)

type Kind string

const (
	KindEmptyDir     Kind = "empty_dir"
	KindBrokenLink   Kind = "broken_symlink"
	KindZeroByteFile Kind = "zero_byte_file"
)

type Finding struct {
	Kind Kind   `json:"kind"`
	Path string `json:"path"`
}

type Scanner interface {
	Name() string
	Scan(root string, path string, info os.FileInfo) ([]Finding, error)
}

func ResolveRoot(path string) (string, error) {
	abs, err := filepath.Abs(path)
	if err != nil {
		return "", fmt.Errorf("resolve path: %w", err)
	}

	info, err := os.Stat(abs)
	if err != nil {
		return "", fmt.Errorf("stat %s: %w", abs, err)
	}
	if !info.IsDir() {
		return "", fmt.Errorf("%s is not a directory", abs)
	}

	return abs, nil
}

func DefaultScanners() []Scanner {
	return []Scanner{
		EmptyDirScanner{},
		BrokenLinkScanner{},
		ZeroByteFileScanner{},
	}
}

func Run(root string, scanners []Scanner) ([]Finding, error) {
	var findings []Finding

	err := filepath.WalkDir(root, func(path string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}

		if entry.Name() == ".git" && entry.IsDir() {
			return filepath.SkipDir
		}

		info, err := entry.Info()
		if err != nil {
			return err
		}

		for _, s := range scanners {
			matches, err := s.Scan(root, path, info)
			if err != nil {
				return fmt.Errorf("%s: %w", s.Name(), err)
			}
			findings = append(findings, matches...)
		}

		return nil
	})
	if err != nil {
		return nil, err
	}

	return findings, nil
}
