# Tests Directory

This directory contains all test files for the Robotics Radar project.

## Structure

### `/unit/`
Unit tests for individual components and modules.

### `/integration/`
Integration tests that test multiple components working together:
- `test_telegram_polling.py` - Tests Telegram bot polling functionality
- `test_feedback_system.py` - Tests the feedback and rating system
- `test_complete_system.py` - End-to-end system tests
- `test_telegram_fixes.py` - Tests for Telegram bot fixes

### `/utilities/`
Utility scripts for testing and debugging:
- `update_article_keywords.py` - Updates keywords for existing articles
- `test_dashboard_features.py` - Tests dashboard functionality
- `check_dashboard_data.py` - Checks dashboard data integrity

## Running Tests

```bash
# Run all tests
./scripts/test.sh

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/utilities/

# Run individual test files
python tests/integration/test_telegram_polling.py
```

## Test Environment

Tests use the same virtual environment as the main application:
```bash
source robotics-radar-env/bin/activate
```

## Notes

- Integration tests may require the application to be running
- Some tests require valid environment variables (Telegram bot token, etc.)
- Database tests use a separate test database to avoid affecting production data 