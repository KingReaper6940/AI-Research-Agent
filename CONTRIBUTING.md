# Contributing to DeepResearch AI Research Agent

Thank you for your interest in contributing to DeepResearch! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/AI-Research-Agent.git
   cd AI-Research-Agent
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

## Running Tests

We use pytest for testing. Run the test suite with:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_credibility.py -v

# Run tests with specific markers
pytest tests/ -m unit -v
```

## Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and modular

## Making Changes

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write tests for new features
   - Update documentation as needed
   - Ensure all tests pass

3. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## Pull Request Guidelines

- **Title**: Use a clear, descriptive title
- **Description**: Explain what changes you made and why
- **Tests**: Ensure all tests pass and add new tests for new features
- **Documentation**: Update README.md or add docstrings as needed

## Types of Contributions

### Bug Fixes
- Check existing issues first
- Include a test that reproduces the bug
- Clearly describe the fix in your PR

### New Features
- Open an issue to discuss the feature first
- Ensure it aligns with the project goals
- Include comprehensive tests
- Update documentation

### Documentation
- Fix typos, improve clarity
- Add examples or better explanations
- Keep it concise and accurate

### Tests
- Improve test coverage
- Add edge case tests
- Improve test organization

## Project Structure

```
├── src/                  # Core application code
│   ├── config.py        # Configuration and settings
│   ├── search.py        # Web and Wikipedia search
│   ├── academic.py      # Academic source search
│   ├── processor.py     # Content processing
│   ├── decomposer.py    # Query decomposition
│   ├── credibility.py   # Source credibility scoring
│   ├── synthesizer.py   # Report synthesis
│   └── agent.py         # Main research agent
├── static/              # Frontend files
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript
│   └── *.html          # HTML pages
├── tests/               # Test suite
├── server.py            # FastAPI server
└── requirements.txt     # Dependencies
```

## Testing Guidelines

- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test full workflows end-to-end
- **Mark Tests**: Use `@pytest.mark.unit` or `@pytest.mark.integration`
- **Coverage**: Aim for >80% code coverage for new code

## Questions?

Feel free to:
- Open an issue for questions
- Ask in your Pull Request
- Check existing issues and PRs

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Help others learn and grow
- Follow the MIT license terms

Thank you for contributing! 🚀
