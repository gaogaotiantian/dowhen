# Documentation

This directory contains the Sphinx documentation for dowhen.

## Building the Documentation

### Prerequisites

Install the documentation requirements:

```bash
pip install -r ../requirements-docs.txt
```

### Building

To build the HTML documentation:

```bash
make html
```

Or from the root directory:

```bash
make docs
```

The built documentation will be available in `_build/html/index.html`.

### Cleaning

To clean the build directory:

```bash
make clean
```

Or from the root directory:

```bash
make docs-clean
```

## Documentation Structure

- `index.rst` - Main documentation index
- `usage.rst` - Usage guide and examples
- `api.rst` - API reference (auto-generated from docstrings)
- `examples.rst` - Comprehensive examples
- `conf.py` - Sphinx configuration
