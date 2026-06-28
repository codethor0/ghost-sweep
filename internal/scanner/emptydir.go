package scanner

import (
	"os"
)

type EmptyDirScanner struct{}

func (EmptyDirScanner) Name() string {
	return "empty_dir"
}

func (EmptyDirScanner) Scan(_ string, path string, info os.FileInfo) ([]Finding, error) {
	if !info.IsDir() {
		return nil, nil
	}

	entries, err := os.ReadDir(path)
	if err != nil {
		return nil, err
	}
	if len(entries) > 0 {
		return nil, nil
	}

	return []Finding{{Kind: KindEmptyDir, Path: path}}, nil
}
