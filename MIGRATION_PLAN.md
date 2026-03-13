# Migration Plan - YouTube Tools Scripts Repository Restructure

## Overview

This document outlines the step-by-step migration plan to restructure the YouTube Tools Scripts repository from its current state to the modern, scalable structure proposed in `REPOSITORY_STRUCTURE_PROPOSAL.md`.

---

## Current State Analysis

### Existing Structure
```
YouTube_Tools_Scripts/
├── Transcripts/              # Output files (mixed with source)
├── Howdy/                    # Staging area
├── yt_processor/             # All scripts mixed together
│   ├── universal_parallel_downloader.py  # New standard
│   ├── universal_chunker.py             # New standard
│   ├── legacy_scripts_backup/            # Old scripts
│   ├── *.py                              # Utility scripts
│   └── tests/                            # Some tests
└── yt-dlp-2025.11.12/       # Dependency
```

### Issues with Current Structure
- ❌ Source code mixed with output data
- ❌ No clear separation between modules
- ❌ Tests scattered
- ❌ No centralized configuration
- ❌ No CI/CD automation
- ❌ Legacy scripts mixed with active code

---

## Migration Strategy

### Approach: Incremental Migration
- **Phase 1**: Create new structure alongside existing
- **Phase 2**: Migrate and refactor code
- **Phase 3**: Update configuration and tooling
- **Phase 4**: Validate and test
- **Phase 5**: Switch over and clean up

### Timeline: 4 Weeks

---

## Phase 1: Foundation (Week 1)

### 1.1 Create New Directory Structure
```bash
# Create new directories
mkdir -p src/youtubetools/{downloader,chunker,processor,utils,cli}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p docs/{api,guides}
mkdir -p config
mkdir -p examples
mkdir -p tools
mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE
```

### 1.2 Create Package Initialization Files
```bash
# Create __init__.py files
touch src/youtubetools/__init__.py
touch src/youtubetools/downloader/__init__.py
touch src/youtubetools/chunker/__init__.py
touch src/youtubetools/processor/__init__.py
touch src/youtubetools/utils/__init__.py
touch src/youtubetools/cli/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/fixtures/__init__.py
```

### 1.3 Create Configuration Files
```bash
# Create pyproject.toml
# Create config/default_config.yaml
# Create config/channels.yaml
# Create config/notebooklm_limits.yaml
# Create .env.example
```

### 1.4 Move Data Directories
```bash
# Move transcript output to data/
mv Transcripts data/transcripts/processed/
mv Howdy data/transcripts/raw/

# Create data subdirectories
mkdir -p data/metadata
mkdir -p data/cache
```

---

## Phase 2: Code Migration (Week 2)

### 2.1 Migrate Downloader Module
**Source**: `yt_processor/universal_parallel_downloader.py`
**Destination**: `src/youtubetools/downloader/universal.py`

**Actions**:
1. Extract VTT parsing logic to `processor/vtt_parser.py`
2. Extract file operations to `utils/file_ops.py`
3. Create `downloader/__init__.py` with exports
4. Add type hints
5. Add docstrings

**Example Refactor**:
```python
# Before: yt_processor/universal_parallel_downloader.py
def clean_vtt_file(vtt_path):
    # ... implementation

# After: src/youtubetools/processor/vtt_parser.py
def clean_vtt_file(vtt_path: Path) -> str:
    """Parse VTT file and extract clean text content."""
    # ... implementation with type hints
```

### 2.2 Migrate Chunker Module
**Source**: `yt_processor/universal_chunker.py`
**Destination**: `src/youtubetools/chunker/universal.py`

**Actions**:
1. Extract Markdown formatting to `processor/markdown.py`
2. Extract configuration to `utils/config.py`
3. Create `chunker/__init__.py` with exports
4. Add type hints
5. Add docstrings

### 2.3 Migrate Processor Module
**New Module**: `src/youtubetools/processor/`

**Actions**:
1. Create `vtt_parser.py` - VTT parsing utilities
2. Create `markdown.py` - Markdown formatting
3. Create `cleaner.py` - Content cleaning
4. Create `__init__.py` with exports

### 2.4 Migrate Utils Module
**New Module**: `src/youtubetools/utils/`

**Actions**:
1. Create `yt_dlp_wrapper.py` - yt-dlp wrapper from `yt_utils.py`
2. Create `file_ops.py` - File operations
3. Create `config.py` - Configuration management
4. Create `__init__.py` with exports

### 2.5 Migrate CLI Module
**New Module**: `src/youtubetools/cli/`

**Actions**:
1. Create `download.py` - Download CLI command
2. Create `chunk.py` - Chunk CLI command
3. Create `main.py` - Main entry point
4. Create `__init__.py` with exports

### 2.6 Move Utility Scripts
**Source**: `yt_processor/*.py` (utility scripts)
**Destination**: `scripts/`

**Actions**:
1. Move analysis scripts to `scripts/`
2. Move categorization scripts to `scripts/`
3. Keep test scripts in `yt_processor/` for now

---

## Phase 3: Configuration and Tooling (Week 3)

### 3.1 Create pyproject.toml
```toml
[project]
name = "youtubetools"
version = "1.0.0"
description = "YouTube transcript processing for NotebookLM"
requires-python = ">=3.11"
dependencies = [
    "yt-dlp>=2024.0.0",
    "requests>=2.31.0",
    "pyyaml>=6.0.0",
    "tqdm>=4.66.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "black>=23.7.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "nox>=2023.4.17",
]

[project.scripts]
yt-download = "youtubetools.cli.download:main"
yt-chunk = "youtubetools.cli.chunk:main"
yt-process = "youtubetools.cli.main:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
ignore = []

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

### 3.2 Create Configuration Files

**config/default_config.yaml**:
```yaml
# Default configuration
downloader:
  workers: 10
  max_retries: 3
  timeout: 300
  use_vtt: true

chunker:
  max_chunk_size: 25165824  # 2.4MB in bytes
  min_chunk_size: 1048576   # 1MB in bytes
  include_toc: true

processor:
  clean_music_tags: true
  remove_timestamps: true
  deduplicate_lines: true
  format: "markdown"

output:
  directory: "data/transcripts/processed"
  naming_pattern: "{channel}_PART_{num:02d}.md"
```

**config/notebooklm_limits.yaml**:
```yaml
# NotebookLM limits
limits:
  max_file_size_mb: 200
  max_words: 500000
  practical_max_mb: 2.5
  practical_max_words: 200000

chunking:
  target_size_mb: 2.4
  safety_margin_mb: 0.1
```

### 3.3 Create CI/CD Workflows

**.github/workflows/test.yml**:
```yaml
name: Tests
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: pytest --cov=src/youtubetools --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

**.github/workflows/lint.yml**:
```yaml
name: Lint
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install black ruff mypy
      
      - name: Run Black
        run: black --check src/ tests/
      
      - name: Run Ruff
        run: ruff check src/ tests/
      
      - name: Run MyPy
        run: mypy src/
```

### 3.4 Create Test Configuration

**tests/conftest.py**:
```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_video_list():
    """Sample video list for testing."""
    return Path("tests/fixtures/sample_video_list.txt")

@pytest.fixture
def sample_transcript():
    """Sample transcript for testing."""
    return Path("tests/fixtures/sample_transcript.vtt")

@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for tests."""
    return tmp_path / "output"
```

### 3.5 Create Development Tools

**tools/setup_env.py**:
```python
#!/usr/bin/env python3
"""Development environment setup script."""
import subprocess
import sys

def main():
    print("Setting up development environment...")
    
    # Install dependencies
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"])
    
    # Install pre-commit hooks
    subprocess.run([sys.executable, "-m", "pip", "install", "pre-commit"])
    subprocess.run(["pre-commit", "install"])
    
    print("✅ Development environment setup complete!")

if __name__ == "__main__":
    main()
```

**tools/run_tests.py**:
```python
#!/usr/bin/env python3
"""Test runner script."""
import subprocess
import sys

def main():
    print("Running tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "--cov=src/youtubetools", "-v"])
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
```

---

## Phase 4: Validation (Week 4)

### 4.1 Create Unit Tests
**tests/unit/test_downloader.py**:
```python
import pytest
from youtubetools.downloader.universal import clean_vtt_file

def test_clean_vtt_file(sample_transcript):
    """Test VTT file cleaning."""
    result = clean_vtt_file(sample_transcript)
    assert isinstance(result, str)
    assert "[Music]" not in result
    assert "-->" not in result
```

**tests/unit/test_chunker.py**:
```python
import pytest
from youtubetools.chunker.universal import create_chunks

def test_create_chunks(sample_video_list):
    """Test chunk creation."""
    chunks = create_chunks(sample_video_list, temp_output_dir)
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.stat().st_size < 2.5 * 1024 * 1024
```

### 4.2 Create Integration Tests
**tests/integration/test_download_workflow.py**:
```python
import pytest
from youtubetools.cli.download import main as download_main

def test_download_workflow():
    """Test end-to-end download workflow."""
    # Test with small sample
    result = download_main(["--list", "tests/fixtures/sample_video_list.txt"])
    assert result == 0
```

### 4.3 Run Full Test Suite
```bash
# Run all tests
pytest --cov=src/youtubetools --cov-report=html

# Check coverage
# Open htmlcov/index.html in browser
```

### 4.4 Verify CLI Commands
```bash
# Test download command
yt-download --help

# Test chunk command
yt-chunk --help

# Test main command
yt-process --help
```

### 4.5 Update Imports
```bash
# Find and replace old imports
# Old: from yt_utils import get_video_metadata
# New: from youtubetools.utils.yt_dlp_wrapper import get_video_metadata
```

---

## Phase 5: Switch Over (Week 4)

### 5.1 Update Documentation
- Update `README.md` with new structure
- Update `yt_processor/README.md` to point to new docs
- Create `docs/migration_guide.md`
- Update `CHANGELOG.md`

### 5.2 Create Migration Guide
**docs/migration_guide.md**:
```markdown
# Migration Guide

## For Users

### Old Command
```bash
python yt_processor/universal_parallel_downloader.py
```

### New Command
```bash
yt-download --list your_video_list.txt
```

## For Developers

### Old Import
```python
from yt_utils import get_video_metadata
```

### New Import
```python
from youtubetools.utils.yt_dlp_wrapper import get_video_metadata
```

## Breaking Changes
- CLI commands changed from Python scripts to installed commands
- Import paths updated to use package structure
- Configuration moved to `config/` directory
```

### 5.3 Archive Old Structure
```bash
# Create archive branch
git checkout -b legacy-archive

# Move old scripts to archive
mv yt_processor/legacy_scripts_backup/* legacy/

# Commit archive
git add .
git commit -m "archive: move legacy scripts to legacy/"
git push origin legacy-archive

# Switch back to main
git checkout main
```

### 5.4 Clean Up Old Files
```bash
# Remove old directories (after verification)
rm -rf yt_processor/legacy_scripts_backup
rm -rf yt_processor/bench_*
rm -rf yt_processor/test_*
rm -rf yt_processor/debug_*
rm -rf yt_processor/accuracy_*
rm -rf yt_processor/final_*
rm -rf yt_processor/verify_*
rm -rf yt_processor/diagnostic_*
rm -rf yt_processor/research_*
rm -rf yt_processor/stress_*
rm -rf yt_processor/api_test_*
rm -rf yt_processor/.pytest_cache
```

### 5.5 Final Verification
```bash
# Run full test suite
pytest --cov=src/youtubetools

# Run linting
ruff check src/ tests/
black --check src/ tests/
mypy src/

# Verify CLI works
yt-download --help
yt-chunk --help
```

### 5.6 Create Release
```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Create tag
git tag v1.0.0
git push origin v1.0.0
```

---

## Rollback Plan

If migration fails, rollback steps:

1. **Restore from backup**:
   ```bash
   git checkout legacy-archive
   git checkout main
   git merge legacy-archive
   ```

2. **Revert changes**:
   ```bash
   git reset --hard HEAD~1
   ```

3. **Restore data**:
   ```bash
   mv data/transcripts/* Transcripts/
   ```

---

## Success Criteria

### Code Quality
- ✅ All tests pass (100%)
- ✅ Code coverage > 80%
- ✅ No linting errors
- ✅ Type checking passes

### Functionality
- ✅ CLI commands work correctly
- ✅ All existing scripts functional
- ✅ No breaking changes for users
- ✅ Documentation complete

### CI/CD
- ✅ All workflows pass
- ✅ Automated testing works
- ✅ Code quality checks pass

---

## Post-Migration Tasks

### Week 5+
1. Add more test coverage
2. Improve documentation
3. Add more examples
4. Set up pre-commit hooks
5. Add performance benchmarks
6. Create contribution guidelines
7. Set up CODEOWNERS

---

## Contact

For questions or issues during migration:
- Create an issue with label `migration`
- Tag `@maintainer-team`
- Include error logs and steps to reproduce

---

## Summary

This migration plan provides:
- ✅ **Incremental approach** - Minimizes disruption
- ✅ **Clear phases** - 4-week timeline
- ✅ **Rollback plan** - Safety net
- ✅ **Success criteria** - Measurable goals
- ✅ **Post-migration tasks** - Continuous improvement

The migration transforms the codebase into a modern, maintainable, and scalable Python package following community best practices.
