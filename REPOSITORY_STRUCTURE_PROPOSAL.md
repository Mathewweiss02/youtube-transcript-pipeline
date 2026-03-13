# YouTube Tools Scripts - Repository Structure Proposal

## Overview

This proposal outlines a modern, scalable repository structure for the YouTube Tools Scripts project, based on Python best practices from the Python community (PyPA, CPython) and tailored for data processing workflows.

---

## Proposed Directory Structure

```
YouTube_Tools_Scripts/
├── .github/                          # GitHub-specific configuration
│   ├── workflows/                   # CI/CD workflows
│   │   ├── test.yml                # Automated testing
│   │   ├── lint.yml                # Code quality checks
│   │   └── release.yml             # Release automation
│   ├── ISSUE_TEMPLATE/             # Issue templates
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md     # PR template
│   └── CODEOWNERS.md               # Code ownership rules
│
├── src/                             # Source code (src-layout pattern)
│   └── youtubetools/               # Main package
│       ├── __init__.py             # Package initialization
│       ├── downloader/             # Download functionality
│       │   ├── __init__.py
│       │   ├── universal.py        # Universal parallel downloader
│       │   ├── production.py       # Production downloader
│       │   └── utils.py            # Download utilities
│       ├── chunker/                # Chunking functionality
│       │   ├── __init__.py
│       │   ├── universal.py        # Universal chunker
│       │   └── utils.py            # Chunking utilities
│       ├── processor/              # Transcript processing
│       │   ├── __init__.py
│       │   ├── vtt_parser.py       # VTT parsing
│       │   ├── markdown.py         # Markdown formatting
│       │   └── cleaner.py          # Content cleaning
│       ├── utils/                  # Shared utilities
│       │   ├── __init__.py
│       │   ├── yt_dlp_wrapper.py   # yt-dlp wrapper
│       │   ├── file_ops.py         # File operations
│       │   └── config.py           # Configuration management
│       └── cli/                    # Command-line interface
│           ├── __init__.py
│           ├── download.py         # Download CLI
│           ├── chunk.py            # Chunk CLI
│           └── main.py             # Main entry point
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── unit/                       # Unit tests
│   │   ├── test_downloader.py
│   │   ├── test_chunker.py
│   │   ├── test_processor.py
│   │   └── test_utils.py
│   ├── integration/                # Integration tests
│   │   ├── test_download_workflow.py
│   │   └── test_chunk_workflow.py
│   └── fixtures/                   # Test fixtures
│       ├── sample_video_list.txt
│       └── sample_transcripts/
│
├── docs/                            # Documentation
│   ├── README.md                   # Main documentation
│   ├── architecture.md             # Architecture overview
│   ├── api/                        # API documentation
│   │   ├── downloader.md
│   │   ├── chunker.md
│   │   └── processor.md
│   ├── guides/                     # User guides
│   │   ├── getting_started.md
│   │   ├── advanced_usage.md
│   │   └── troubleshooting.md
│   └── contributing.md             # Contribution guidelines
│
├── scripts/                         # Standalone scripts (legacy support)
│   ├── download_mark_bell_vtt.py   # Channel-specific downloads
│   ├── convert_raw_transcripts.py  # Conversion utilities
│   └── analyze_*.py                # Analysis scripts
│
├── config/                          # Configuration files
│   ├── default_config.yaml         # Default configuration
│   ├── channels.yaml               # Channel configurations
│   └── notebooklm_limits.yaml      # NotebookLM limits
│
├── data/                            # Data storage (gitignored)
│   ├── transcripts/                # Downloaded transcripts
│   │   ├── raw/                    # Raw downloads
│   │   └── processed/              # Processed chunks
│   ├── metadata/                   # Video metadata
│   └── cache/                      # Download cache
│
├── examples/                        # Example usage
│   ├── basic_download.py
│   ├── custom_chunking.py
│   └── batch_processing.py
│
├── tools/                           # Development tools
│   ├── setup_env.py                # Environment setup
│   ├── run_tests.py                # Test runner
│   └── format_code.py              # Code formatting
│
├── .gitignore                       # Git ignore rules
├── .env.example                     # Environment variables template
├── LICENSE.txt                      # Project license
├── pyproject.toml                   # Project configuration
├── requirements.txt                 # Dependencies
├── requirements-dev.txt             # Development dependencies
├── noxfile.py                       # Development task automation
├── README.md                        # Project README
└── CHANGELOG.md                     # Version history
```

---

## Directory Purposes

### Top-Level Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `.github/` | GitHub configuration | CI/CD workflows, templates, CODEOWNERS |
| `src/` | Source code | Main package with modular components |
| `tests/` | Test suite | Unit, integration, and fixture files |
| `docs/` | Documentation | User guides, API docs, architecture |
| `scripts/` | Standalone scripts | Legacy scripts and utilities |
| `config/` | Configuration | YAML config files |
| `data/` | Data storage | Transcripts, metadata, cache (gitignored) |
| `examples/` | Examples | Sample usage patterns |
| `tools/` | Development tools | Setup, testing, formatting utilities |

### Source Code Modules (`src/youtubetools/`)

| Module | Purpose | Key Functions |
|--------|---------|--------------|
| `downloader/` | YouTube transcript downloads | Parallel downloading, VTT handling |
| `chunker/` | Transcript chunking | NotebookLM-compliant chunking |
| `processor/` | Content processing | VTT parsing, Markdown formatting |
| `utils/` | Shared utilities | yt-dlp wrapper, file operations |
| `cli/` | Command-line interface | User-facing commands |

---

## Naming Conventions

### Files
- **Python modules**: `snake_case.py`
- **Test files**: `test_<module_name>.py`
- **Configuration**: `kebab-case.yaml`
- **Documentation**: `kebab-case.md`
- **Scripts**: `snake_case.py`

### Directories
- **Packages**: `snake_case`
- **Test directories**: `unit/`, `integration/`, `fixtures/`
- **Data directories**: `raw/`, `processed/`, `metadata/`

### Code
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

---

## Configuration Files

### `pyproject.toml` (Primary Configuration)
```toml
[project]
name = "youtubetools"
version = "1.0.0"
description = "YouTube transcript processing for NotebookLM"
requires-python = ">=3.11"
dependencies = [
    "yt-dlp>=2024.0.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.7.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[project.scripts]
yt-download = "youtubetools.cli.download:main"
yt-chunk = "youtubetools.cli.chunk:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
```

### `config/default_config.yaml`
```yaml
# Default configuration
downloader:
  workers: 10
  max_retries: 3
  timeout: 300

chunker:
  max_chunk_size: 25165824  # 2.4MB in bytes
  min_chunk_size: 1048576   # 1MB in bytes

processor:
  clean_music_tags: true
  remove_timestamps: true
  deduplicate_lines: true
```

---

## Dependency Management

### Production Dependencies (`requirements.txt`)
```
yt-dlp>=2024.0.0
requests>=2.31.0
pyyaml>=6.0.0
tqdm>=4.66.0
```

### Development Dependencies (`requirements-dev.txt`)
```
-r requirements.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
black>=23.7.0
ruff>=0.1.0
mypy>=1.5.0
nox>=2023.4.17
```

---

## Testing Strategy

### Test Organization
```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_downloader.py
│   ├── test_chunker.py
│   └── test_processor.py
├── integration/       # End-to-end tests
│   ├── test_download_workflow.py
│   └── test_chunk_workflow.py
└── fixtures/          # Test data
    ├── sample_video_list.txt
    └── sample_transcripts/
```

### Test Execution
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/youtubetools --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run with verbose output
pytest -v
```

### CI/CD Integration (`.github/workflows/test.yml`)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=src/youtubetools
```

---

## CI/CD Integration Points

### Workflows (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `test.yml` | Push/PR | Run tests and linting |
| `lint.yml` | Push/PR | Code quality checks |
| `release.yml` | Tag | Build and publish |

### Quality Gates
- All tests must pass
- Code coverage > 80%
- No linting errors
- Type checking passes (mypy)

---

## Documentation Placement

### User Documentation (`docs/`)
- `README.md` - Quick start guide
- `guides/getting_started.md` - Detailed setup
- `guides/advanced_usage.md` - Advanced features
- `guides/troubleshooting.md` - Common issues

### Developer Documentation (`docs/`)
- `architecture.md` - System architecture
- `api/` - API reference
- `contributing.md` - Contribution guide

### Inline Documentation
- Docstrings for all modules, classes, functions
- Type hints for function signatures
- Comments for complex logic

---

## Modularization Approach

### Principles
1. **Single Responsibility** - Each module has one clear purpose
2. **Loose Coupling** - Modules interact through well-defined interfaces
3. **High Cohesion** - Related functionality grouped together
4. **Dependency Injection** - Pass dependencies rather than hardcode

### Module Dependencies
```
cli/
  ├── downloader/
  │   └── utils/
  ├── chunker/
  │   └── processor/
  │       └── utils/
  └── utils/
```

---

## Examples and Sample Data

### Location: `examples/`
- `basic_download.py` - Simple download example
- `custom_chunking.py` - Custom chunk size example
- `batch_processing.py` - Batch processing example

### Sample Data: `tests/fixtures/`
- `sample_video_list.txt` - Test video list
- `sample_transcripts/` - Sample transcript files

---

## Versioning and Release Workflow

### Semantic Versioning
- Format: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Process
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. CI/CD automatically builds and publishes

### Changelog Format (`CHANGELOG.md`)
```markdown
## [1.0.0] - 2024-01-09
### Added
- Universal parallel downloader
- Universal chunker for NotebookLM
- VTT format support

### Changed
- Migrated all legacy scripts to backup

### Fixed
- File locking issues during downloads
```

---

## Issue and PR Labels

### Issue Labels
- `bug` - Bug reports
- `enhancement` - Feature requests
- `documentation` - Documentation issues
- `performance` - Performance improvements
- `good first issue` - Good for newcomers
- `help wanted` - Community help needed

### PR Labels
- `bugfix` - Bug fix PRs
- `feature` - New feature PRs
- `refactor` - Code refactoring
- `documentation` - Documentation updates
- `breaking-change` - Breaking changes
- `needs-review` - Awaiting review

---

## Access and Permissions

### CODEOWNERS (`.github/CODEOWNERS.md`)
```
# Core modules
src/youtubetools/downloader/ @maintainer-team
src/youtubetools/chunker/ @maintainer-team

# Documentation
docs/ @docs-team

# CI/CD
.github/workflows/ @devops-team
```

### Branch Protection
- `main` branch requires:
  - PR reviews (1 approval)
  - CI/CD checks passing
  - No direct commits

---

## Metadata Files

### Required Files
- `pyproject.toml` - Project metadata and configuration
- `README.md` - Project documentation
- `LICENSE.txt` - License information
- `.gitignore` - Git ignore rules
- `CHANGELOG.md` - Version history

### Optional Files
- `.env.example` - Environment variables template
- `AUTHORS.md` - Contributors list
- `CONTRIBUTING.md` - Contribution guidelines

---

## Migration Plan

### Phase 1: Restructure (Week 1)
1. Create new directory structure
2. Move source code to `src/youtubetools/`
3. Move tests to `tests/`
4. Move documentation to `docs/`

### Phase 2: Refactor (Week 2)
1. Modularize code into packages
2. Add type hints
3. Update imports
4. Create CLI entry points

### Phase 3: Configure (Week 3)
1. Create `pyproject.toml`
2. Set up CI/CD workflows
3. Configure testing tools
4. Add linting configuration

### Phase 4: Validate (Week 4)
1. Run all tests
2. Verify CI/CD passes
3. Update documentation
4. Create release notes

---

## Onboarding Checklist

### For New Contributors

**Setup (5 minutes)**
- [ ] Clone repository: `git clone <repo-url>`
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate environment: `venv\Scripts\activate` (Windows)
- [ ] Install dependencies: `pip install -r requirements-dev.txt`

**Development (10 minutes)**
- [ ] Run tests: `pytest`
- [ ] Run linting: `ruff check src/`
- [ ] Format code: `black src/`
- [ ] Type check: `mypy src/`

**Contribution (15 minutes)**
- [ ] Create feature branch: `git checkout -b feature/my-feature`
- [ ] Make changes following naming conventions
- [ ] Add/update tests
- [ ] Update documentation
- [ ] Run full test suite: `pytest --cov`
- [ ] Commit changes: `git commit -m "feat: add my feature"`
- [ ] Push branch: `git push origin feature/my-feature`
- [ ] Create pull request with template

**PR Review Checklist**
- [ ] Tests pass locally
- [ ] Code follows style guide (black, ruff)
- [ ] Type hints added
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] No breaking changes without discussion

---

## Pragmatic Steps for Migration

### Immediate Actions
1. **Backup current state**: Create a branch `legacy-backup`
2. **Create new structure**: Set up directories
3. **Move source code**: Migrate to `src/youtubetools/`
4. **Update imports**: Fix all import statements
5. **Create configuration**: Set up `pyproject.toml`

### Validation Actions
1. **Run tests**: Ensure all tests pass
2. **Check imports**: Verify no broken imports
3. **Test CLI**: Verify commands work
4. **Update docs**: Document new structure

### Final Actions
1. **Update README**: Reflect new structure
2. **Create migration guide**: Document changes
3. **Announce changes**: Notify team
4. **Archive legacy**: Move old scripts to `legacy/`

---

## Summary

This repository structure proposal provides:
- ✅ **Modular organization** - Clear separation of concerns
- ✅ **Modern Python practices** - src-layout, pyproject.toml
- ✅ **Comprehensive testing** - Unit, integration, fixtures
- ✅ **CI/CD integration** - Automated testing and quality checks
- ✅ **Clear documentation** - User and developer guides
- ✅ **Scalable architecture** - Easy to extend and maintain
- ✅ **Standard conventions** - Follows Python community best practices

The structure balances simplicity for small scripts with scalability for future growth, making it easy for new contributors to get started while maintaining code quality and organization.
