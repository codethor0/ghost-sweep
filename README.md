# ghost-sweep

CLI utility for finding orphaned and stale filesystem artifacts.

## Requirements

- Go 1.26+

## Build

```bash
go build -o ghost-sweep ./cmd/ghost-sweep
```

## Usage

```bash
# Scan the current directory
./ghost-sweep

# Scan a specific path
./ghost-sweep --path ~/Projects

# JSON output
./ghost-sweep --path . --json
```

## Detectors

| Kind | Description |
|------|-------------|
| `empty_dir` | Directories with no entries |
| `broken_symlink` | Symlinks whose targets are missing |
| `zero_byte_file` | Regular files with size 0 |

## License

MIT
