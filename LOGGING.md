# Logging Framework

This document describes the centralized logging framework for biosample-enricher.

## Overview

The logging framework provides a simple, mainstream approach to logging using Python's standard `logging` library. It supports both console and file output with configurable levels and automatic log rotation.

## Basic Usage

### Setup Logging

```python
from biosample_enricher.logging_config import setup_logging

# Basic setup with defaults
logger = setup_logging()

# Custom configuration
logger = setup_logging(
    level="DEBUG",
    log_file="my_app.log",
    enable_file_logging=True
)
```

### Get Module Logger

```python
from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)
logger.info("This is an info message")
logger.debug("This is a debug message")
logger.warning("This is a warning")
logger.error("This is an error")
```

### Environment Configuration

Configure logging via environment variables:

```bash
export LOG_LEVEL=DEBUG
export LOG_FILE=biosample_enricher.log
export DISABLE_FILE_LOGGING=1  # To disable file logging
```

Then use:

```python
from biosample_enricher.logging_config import configure_from_env

logger = configure_from_env()
```

## Configuration Options

### Log Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Something unexpected happened but the program continues
- `ERROR`: A serious problem occurred
- `CRITICAL`: A very serious error occurred

### Output Formats

**Console Format:**
```
2025-01-10 14:30:45 - biosample_enricher.core - INFO - Enriching sample ABC123
```

**File Format:**
```
2025-01-10 14:30:45 - biosample_enricher.core - INFO - /path/to/core.py:62 - Enriching sample ABC123
```

### File Logging Features

- **Automatic rotation**: Files are rotated when they reach 10MB
- **Backup retention**: Keeps 5 backup files
- **Directory creation**: Log directories are created automatically
- **Full debug logging**: File gets all log levels, console respects configured level

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level for console output |
| `LOG_FILE` | `biosample_enricher.log` | Path to log file |
| `DISABLE_FILE_LOGGING` | Not set | Set to any value to disable file logging |

## Usage Examples

### Basic Application Logging

```python
from biosample_enricher.logging_config import setup_logging, get_logger

# Set up logging at application start
setup_logging(level="INFO")

# In your modules
logger = get_logger(__name__)

def process_sample(sample_id):
    logger.info(f"Processing sample {sample_id}")
    try:
        # ... processing code ...
        logger.debug("Processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Failed to process sample {sample_id}: {e}")
        raise
```

### Avoid These Anti-Patterns

```python
# DON'T DO THIS - Use logging instead
print(f"Processing sample {sample_id}")
click.echo(f"Error: {error_message}")

# DO THIS INSTEAD
logger.info(f"Processing sample {sample_id}")
logger.error(f"Error: {error_message}")

# Rich console is OK for user interaction in CLI
from rich.console import Console
console = Console()
console.print("[green]✅ Operation completed successfully[/green]")  # CLI feedback
logger.info("Operation completed successfully")  # Application logging
```

### HTTP Request Logging

The HTTP cache module automatically logs:

```python
from biosample_enricher.http_cache import request

# This will log:
# DEBUG: Making GET request to https://api.example.com
# DEBUG: GET https://api.example.com -> 200 (Cache: MISS)
response = request("GET", "https://api.example.com/data")
```

### Coordinate Canonicalization Logging

```python
# When coordinates are canonicalized, this is logged:
# DEBUG: Canonicalized coordinates: {'lat': 37.774929} -> {'lat': 37.7749}
```

## Testing

The logging framework includes comprehensive tests:

```bash
# Run logging tests
uv run pytest tests/test_logging.py -v

# Run with network tests (for HTTP request logging)
uv run pytest tests/test_logging.py -m network -v
```

## Integration with Existing Code

The logging framework is integrated into key modules:

- **core.py**: Logs enrichment operations and batch processing
- **http_cache.py**: Logs cache backend selection, requests, and coordinate canonicalization
- **cache_management.py**: Could be extended with logging for CLI operations

## Best Practices

1. **Use module-level loggers**: Always use `get_logger(__name__)` in each module
2. **Appropriate log levels**: 
   - Use `DEBUG` for detailed tracing
   - Use `INFO` for important business logic events
   - Use `WARNING` for recoverable issues
   - Use `ERROR` for serious problems
3. **Include context**: Log relevant IDs, parameters, and state information
4. **Don't log sensitive data**: Be careful with API keys, passwords, etc.
5. **Use structured logging**: Include key-value pairs for better searchability
6. **Avoid print() and click.echo()**: Use the logging framework instead of print statements or click.echo() for consistent formatting and proper log levels
7. **Rich console for user interaction only**: Reserve Rich console output for direct user interaction (CLI progress, help text), not for application logging

## Log File Management

- Log files are automatically rotated at 10MB
- 5 backup files are retained (e.g., `app.log.1`, `app.log.2`, etc.)
- Older backups are automatically deleted
- Use external tools like `logrotate` for more complex rotation needs

## Troubleshooting

### No log file created
- Check file permissions in the log directory
- Verify `DISABLE_FILE_LOGGING` is not set
- Check disk space

### Missing log messages
- Verify log level configuration
- Check that logger names match module names
- Ensure `setup_logging()` was called before logging

### Performance concerns
- File logging has minimal performance impact
- Use appropriate log levels in production
- Consider disabling DEBUG logging in production for better performance