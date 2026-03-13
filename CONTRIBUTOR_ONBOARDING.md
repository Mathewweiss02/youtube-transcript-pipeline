# Contributor Onboarding Checklist

## Quick Start (5 Minutes)

### Prerequisites
- [ ] Python 3.11 or higher installed
- [ ] Git installed and configured
- [ ] GitHub account
- [ ] Text editor (VS Code recommended)

### Clone Repository
```bash
git clone https://github.com/yourusername/YouTube_Tools_Scripts.git
cd YouTube_Tools_Scripts
```

---

## Environment Setup (10 Minutes)

### 1. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Or install with optional dev dependencies
pip install -e ".[dev]"
```

### 3. Verify Installation
```bash
# Check Python version
python --version  # Should be 3.11+

# Check installed packages
pip list

# Test CLI commands
yt-download --help
yt-chunk --help
```

---

## Development Setup (15 Minutes)

### 1. Configure Git
```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2. Set Up Pre-commit Hooks (Optional)
```bash
pip install pre-commit
pre-commit install
```

### 3. Run Development Tools
```bash
# Run tests
pytest

# Run linting
ruff check src/ tests/
black --check src/ tests/

# Run type checking
mypy src/
```

### 4. Create Development Branch
```bash
git checkout -b feature/my-feature
```

---

## Understanding the Codebase (20 Minutes)

### 1. Read Documentation
- [ ] `README.md` - Project overview
- [ ] `docs/architecture.md` - System architecture
- [ ] `docs/guides/getting_started.md` - Getting started guide
- [ ] `REPOSITORY_STRUCTURE_PROPOSAL.md` - Repository structure

### 2. Explore Source Code
```
src/youtubetools/
├── downloader/    # YouTube transcript downloads
├── chunker/       # Transcript chunking
├── processor/     # Content processing
├── utils/         # Shared utilities
└── cli/           # Command-line interface
```

### 3. Review Key Modules
- [ ] `src/youtubetools/downloader/universal.py` - Universal downloader
- [ ] `src/youtubetools/chunker/universal.py` - Universal chunker
- [ ] `src/youtubetools/processor/vtt_parser.py` - VTT parsing
- [ ] `src/youtubetools/utils/yt_dlp_wrapper.py` - yt-dlp wrapper

### 4. Understand Configuration
- [ ] `config/default_config.yaml` - Default settings
- [ ] `config/notebooklm_limits.yaml` - NotebookLM limits
- [ ] `pyproject.toml` - Project configuration

---

## Running Tests (10 Minutes)

### 1. Run All Tests
```bash
pytest
```

### 2. Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_downloader.py
```

### 3. Run with Coverage
```bash
pytest --cov=src/youtubetools --cov-report=html
```

### 4. Run with Verbose Output
```bash
pytest -v
```

### 5. Run with Specific Marker
```bash
pytest -m "not slow"
```

---

## Code Quality Checks (10 Minutes)

### 1. Format Code with Black
```bash
# Check formatting
black --check src/ tests/

# Auto-format code
black src/ tests/
```

### 2. Lint with Ruff
```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

### 3. Type Check with MyPy
```bash
mypy src/
```

### 4. Run All Quality Checks
```bash
# Combined check
ruff check src/ tests/ && black --check src/ tests/ && mypy src/
```

---

## Making Changes (30 Minutes)

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- [ ] Follow naming conventions (snake_case for files/functions)
- [ ] Add type hints to function signatures
- [ ] Add docstrings to functions and classes
- [ ] Keep functions focused and small
- [ ] Add tests for new functionality

### 3. Write Tests
```python
# Example test
import pytest
from youtubetools.downloader.universal import clean_vtt_file

def test_clean_vtt_file():
    """Test VTT file cleaning."""
    result = clean_vtt_file("test.vtt")
    assert "[Music]" not in result
```

### 4. Run Tests
```bash
pytest
```

### 5. Run Quality Checks
```bash
black src/ tests/
ruff check --fix src/ tests/
mypy src/
```

### 6. Commit Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

### Commit Message Format
```
<type>: <description>

[optional body]

[optional footer]

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes (formatting)
- refactor: Code refactoring
- test: Adding or updating tests
- chore: Maintenance tasks
```

---

## Submitting a Pull Request (20 Minutes)

### 1. Push Your Branch
```bash
git push origin feature/your-feature-name
```

### 2. Create Pull Request
- Go to GitHub repository
- Click "New Pull Request"
- Select your branch
- Fill out PR template

### 3. PR Checklist
- [ ] Title follows convention: `feat: your feature`
- [ ] Description explains the change
- [ ] Linked to relevant issue (if applicable)
- [ ] All tests pass locally
- [ ] Code follows style guide (black, ruff)
- [ ] Type hints added
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] No breaking changes without discussion

### 4. PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Added tests
- [ ] All tests pass
```

---

## Common Tasks

### Adding a New Download Feature
1. Add function to `src/youtubetools/downloader/`
2. Add tests to `tests/unit/test_downloader.py`
3. Update `docs/api/downloader.md`
4. Run tests and quality checks
5. Submit PR

### Adding a New Chunking Strategy
1. Add function to `src/youtubetools/chunker/`
2. Add tests to `tests/unit/test_chunker.py`
3. Update `docs/api/chunker.md`
4. Run tests and quality checks
5. Submit PR

### Updating Configuration
1. Modify `config/default_config.yaml`
2. Update `docs/guides/configuration.md`
3. Add tests for new config options
4. Run tests and quality checks
5. Submit PR

### Fixing a Bug
1. Create branch: `bugfix/bug-description`
2. Add test that reproduces bug
3. Fix the bug
4. Verify test passes
5. Run all tests
6. Submit PR with label `bugfix`

---

## Troubleshooting

### Import Errors
```bash
# Reinstall package in development mode
pip install -e .
```

### Test Failures
```bash
# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_downloader.py::test_function_name

# Run with pdb debugger
pytest --pdb
```

### Linting Errors
```bash
# Auto-fix ruff issues
ruff check --fix src/ tests/

# Format with black
black src/ tests/
```

### Type Checking Errors
```bash
# Check specific file
mypy src/youtubetools/downloader/universal.py

# Ignore specific errors
# Add: # type: ignore
```

---

## Getting Help

### Documentation
- `README.md` - Project overview
- `docs/guides/getting_started.md` - Getting started
- `docs/guides/troubleshooting.md` - Common issues
- `docs/api/` - API documentation

### Community
- GitHub Issues - Report bugs and request features
- GitHub Discussions - Ask questions and share ideas
- CODEOWNERS - See who owns which code

### Resources
- Python Documentation: https://docs.python.org/
- yt-dlp Documentation: https://github.com/yt-dlp/yt-dlp
- PyPA Packaging: https://packaging.python.org/

---

## Best Practices

### Code Style
- Follow PEP 8
- Use Black for formatting
- Use Ruff for linting
- Add type hints
- Write docstrings

### Testing
- Write tests for all new code
- Aim for >80% code coverage
- Test edge cases
- Use descriptive test names

### Documentation
- Update README for user-facing changes
- Update API docs for new functions
- Add examples for new features
- Document breaking changes

### Git
- Use descriptive commit messages
- Keep commits focused
- Write good PR descriptions
- Review your own PRs before submitting

---

## Quick Reference Commands

### Development
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black src/ tests/

# Lint code
ruff check --fix src/ tests/

# Type check
mypy src/
```

### Git
```bash
# Create branch
git checkout -b feature/my-feature

# Commit changes
git add .
git commit -m "feat: add feature"

# Push branch
git push origin feature/my-feature
```

### CLI
```bash
# Download transcripts
yt-download --list video_list.txt

# Chunk transcripts
yt-chunk --input raw/ --output processed/

# Process transcripts
yt-process --config config/default_config.yaml
```

---

## Completion Checklist

Before submitting your first PR, ensure you've:

### Setup
- [ ] Cloned repository
- [ ] Created virtual environment
- [ ] Installed dependencies
- [ ] Configured git

### Development
- [ ] Read documentation
- [ ] Explored codebase
- [ ] Created feature branch
- [ ] Made changes
- [ ] Added tests
- [ ] Ran tests
- [ ] Ran quality checks

### Submission
- [ ] Committed changes
- [ ] Pushed branch
- [ ] Created PR
- [ ] Filled out PR template
- [ ] Linked to issue (if applicable)

---

## Next Steps

After completing onboarding:

1. **Start Small** - Fix a bug or add a small feature
2. **Ask Questions** - Use GitHub Discussions for help
3. **Review PRs** - Help review other contributors' PRs
4. **Contribute** - Regular contributions help the project grow

---

## Contact

For questions or help:
- Create a GitHub Issue
- Start a GitHub Discussion
- Tag maintainainers in PRs

---

**Welcome to the YouTube Tools Scripts community!** 🚀

We're excited to have you contribute. If you have any questions, don't hesitate to ask.
