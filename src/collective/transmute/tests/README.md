# Tests for Collective Transmute Examples

This directory contains comprehensive tests for all the examples provided in the `examples/` directory. The tests ensure that the migration examples work correctly and demonstrate proper usage.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── pytest.ini                 # Pytest configuration
├── run_tests.py               # Test runner script
├── README.md                  # This file
├── test_workflow_migration.py # Tests for workflow migration examples
├── test_content_type_migration.py # Tests for content type migration
├── test_multi_site_migration.py   # Tests for multi-site migration
└── test_incremental_migration.py  # Tests for incremental migration
```

## Running Tests

### Prerequisites

Install the required testing dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Basic Test Execution

Run all tests:

```bash
# Using pytest directly
pytest tests/

# Using the test runner script
python tests/run_tests.py

# Using the test runner with specific test type
python tests/run_tests.py --test-type all
```

### Running Specific Test Categories

```bash
# Run only unit tests
python tests/run_tests.py --test-type unit

# Run only integration tests
python tests/run_tests.py --test-type integration

# Run workflow migration tests
python tests/run_tests.py --test-type workflow

# Run content type migration tests
python tests/run_tests.py --test-type content-type

# Run multi-site migration tests
python tests/run_tests.py --test-type multi-site

# Run incremental migration tests
python tests/run_tests.py --test-type incremental
```

### Test Options

```bash
# Run with coverage report
python tests/run_tests.py --coverage

# Run with HTML coverage report
python tests/run_tests.py --coverage --html-report

# Run with verbose output
python tests/run_tests.py --verbose

# Skip slow tests
python tests/run_tests.py --fast
```

### Using pytest directly

```bash
# Run all tests with coverage
pytest tests/ --cov=examples --cov=collective.transmute --cov-report=html

# Run specific test file
pytest tests/test_workflow_migration.py -v

# Run specific test class
pytest tests/test_workflow_migration.py::TestCustomWorkflowProcessor -v

# Run specific test method
pytest tests/test_workflow_migration.py::TestCustomWorkflowProcessor::test_basic_workflow_processing -v

# Run tests matching a pattern
pytest tests/ -k "workflow" -v

# Run async tests only
pytest tests/ -m asyncio

# Run integration tests only
pytest tests/ -m integration
```

## Test Categories

### 1. Workflow Migration Tests (`test_workflow_migration.py`)

Tests for workflow state migration, including:
- Custom workflow processor functionality
- Workflow state mapping
- Workflow history cleanup
- Workflow transitions processing
- Advanced workflow processor features
- Configuration loading and validation
- Integration scenarios

### 2. Content Type Migration Tests (`test_content_type_migration.py`)

Tests for content type transformation, including:
- Custom content type processors
- Field mapping functionality
- Content type routing logic
- Text field processing
- Creators and subjects field handling
- Configuration validation
- Multiple content type migration

### 3. Multi-Site Migration Tests (`test_multi_site_migration.py`)

Tests for multi-site migration scenarios, including:
- MultiSiteMigrator class functionality
- Site-specific configuration loading
- Error handling and recovery
- Summary report generation
- Configuration validation
- Integration testing

### 4. Incremental Migration Tests (`test_incremental_migration.py`)

Tests for incremental migration functionality, including:
- IncrementalMigrator class features
- State management and persistence
- Item hash generation and modification detection
- Batch processing
- CLI interface testing
- Error handling and recovery
- End-to-end integration testing

## Test Fixtures

The `conftest.py` file provides common fixtures used across all tests:

- `temp_dir`: Temporary directory for test files
- `sample_plone_item`: Sample Plone item for testing
- `sample_news_item`: Sample News Item for testing
- `sample_event_item`: Sample Event for testing
- `sample_custom_news_item`: Sample custom news item
- `sample_workflow_item`: Sample item with workflow history
- `sample_metadata_info`: Sample metadata information
- `mock_console`: Mock console for testing
- `sample_source_files`: Sample source files for testing
- `workflow_config`: Sample workflow configuration
- `content_type_config`: Sample content type configuration
- `mock_pipeline_state`: Mock pipeline state
- `sample_migration_results`: Sample migration results

## Test Coverage

The tests provide comprehensive coverage of:

- **Unit Tests**: Individual function and method testing
- **Integration Tests**: End-to-end workflow testing
- **Error Handling**: Exception and error condition testing
- **Configuration**: Configuration loading and validation
- **CLI Interface**: Command-line interface testing
- **State Management**: State persistence and recovery
- **Data Processing**: Data transformation and validation

## Continuous Integration

The tests are designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio pytest-cov pytest-mock
      - name: Run tests
        run: |
          pytest tests/ --cov=examples --cov=collective.transmute --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## Debugging Tests

To debug failing tests:

```bash
# Run with maximum verbosity
pytest tests/ -vvv

# Run with print statement output
pytest tests/ -s

# Run specific failing test
pytest tests/test_workflow_migration.py::TestCustomWorkflowProcessor::test_basic_workflow_processing -vvv -s

# Run with debugger
pytest tests/ --pdb
```

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention: `test_*.py`
2. Use descriptive test method names
3. Add appropriate docstrings
4. Use the provided fixtures when possible
5. Add appropriate markers (`@pytest.mark.asyncio`, `@pytest.mark.integration`, etc.)
6. Ensure tests are isolated and don't depend on external state
7. Add both positive and negative test cases
8. Test error conditions and edge cases

## Test Maintenance

- Keep tests up to date with example changes
- Ensure tests reflect real-world usage scenarios
- Maintain good test coverage
- Review and update tests when adding new features
- Remove obsolete tests when examples are removed 