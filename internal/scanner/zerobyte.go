package scanner

import (
	"os"
)

type ZeroByteFileScanner struct{}

func (ZeroByteFileScanner) Name() string {
	return "zero_byte_file"
}

func (ZeroByteFileScanner) Scan(_ string, path string, info os.FileInfo) ([]Finding, error) {
	if info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
		return nil, nil
	}
	if info.Size() > 0 {
		return nil, nil
	}

	return []Finding{{Kind: KindZeroByteFile, Path: path}}, nil
}
