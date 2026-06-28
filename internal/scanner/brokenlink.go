package scanner

import (
	"os"
)

type BrokenLinkScanner struct{}

func (BrokenLinkScanner) Name() string {
	return "broken_symlink"
}

func (BrokenLinkScanner) Scan(_ string, path string, info os.FileInfo) ([]Finding, error) {
	if info.Mode()&os.ModeSymlink == 0 {
		return nil, nil
	}

	target, err := os.Readlink(path)
	if err != nil {
		return nil, err
	}

	if _, err := os.Stat(path); err == nil {
		return nil, nil
	}

	return []Finding{{Kind: KindBrokenLink, Path: path + " -> " + target}}, nil
}
