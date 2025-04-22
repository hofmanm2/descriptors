# Python Descriptors and Decorators Library

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive collection of reusable Python descriptors and decorators designed to enhance code reliability, readability, and functionality. This library provides tools for robust exception handling, safe module imports, and other common programming patterns.

## 🚀 Features

- **Error Handling**: Catch and manage exceptions gracefully with detailed logging and tracking
- **Safe Imports**: Import modules safely without crashing when dependencies are missing
- **Debugging Support**: Track and analyze exceptions across your application
- **Minimal Dependencies**: Zero external dependencies - works with standard Python libraries

## 📦 Installation

Currently this package is not published to PyPI. Install directly from the repository:

```bash
git clone https://github.com/yourusername/descriptors.git
cd descriptors
pip install -e .
```

## 🔧 Components

### 1. `safe_catch` Decorator

A powerful decorator for comprehensive exception handling with extended capabilities:

#### Features

- **Exception Suppression**: Catch exceptions and continue execution
- **Custom Logging**: Log exceptions with configurable messages and log levels
- **Exception Tracking**: Store exception history for debugging and analysis
- **Global Registry**: Track exceptions across your entire application
- **Context Manager**: Use with `with` statements for temporary exception handling
- **Class Decoration**: Apply exception handling to all methods in a class
- **Detailed Context**: Capture function arguments and execution context

#### Usage Examples

```python
from decorators import safe_catch

# Basic usage
@safe_catch
def divide(a, b):
    return a / b

# Parameterized decorator
@safe_catch(message="Division error", track_globally=True)
def advanced_divide(a, b):
    return a / b

# Non-suppressing (re-raises exceptions)
@safe_catch(suppress=False)
def validate(value):
    assert value > 0, "Value must be positive"
    return value

# Class decoration
@safe_catch(message="Calculator error")
class Calculator:
    def divide(self, a, b):
        return a / b

# Context manager
with safe_catch(message="Operation failed") as catcher:
    result = 10 / 0
    
# Access caught exceptions
exceptions = catcher.get_exceptions()
```

### 2. `safe_import` Utility

A descriptor-based utility for safely importing modules without raising exceptions when dependencies are unavailable:

#### Features

- **Graceful Fallback**: Returns `None` instead of raising exceptions for unavailable modules
- **Alias Support**: Import modules under alternative names
- **Namespace Control**: Prevent accidental overwriting of existing variables
- **Custom Globals**: Import into a specific globals dictionary
- **Nested Modules**: Support for importing deeply nested submodules

#### Usage Examples

```python
from decorators import safe_import

# Basic usage
numpy = safe_import('numpy')
if numpy:
    print(f"NumPy version: {numpy.__version__}")
else:
    print("NumPy not available")

# With alias
pd = safe_import('pandas', alias='pd')

# Custom globals dictionary
my_globals = {}
safe_import('datetime', globals_dict=my_globals)

# Prevent overwriting existing variables
globals()['json'] = "Not the json module"
json_module = safe_import('json', overwrite=False)
# json variable remains unchanged

# Nested submodule import
xml_etree = safe_import('xml.etree.ElementTree')
```

### 3. Exception Management

The library provides tools for tracking and analyzing exceptions:

#### ExceptionRegistry

```python
from decorators import ExceptionRegistry

# Get all exceptions caught with track_globally=True
all_exceptions = ExceptionRegistry.get_exceptions()

# Examine exception details
for exception in all_exceptions:
    print(f"{exception.timestamp}: {exception.context}")
    print(f"  {exception.exc_type.__name__}: {exception.exc_val}")
    
# Clear exception history
ExceptionRegistry.clear_exceptions()
```

## 🧪 Running Tests

The project uses Python's built-in unittest framework for testing. Run the tests with:

```bash
python -m unittest discover tests
```

Or use the VS Code testing interface which is already configured in the workspace settings.

## 📝 Examples

Explore full example programs demonstrating all features:

- [`example_safe_catch.py`](example_safe_catch.py) - Shows the capabilities of the `safe_catch` decorator
- [`example_safe_import.py`](example_safe_import.py) - Demonstrates the `safe_import` utility

## 📋 Requirements

- Python 3.9 or higher
- No external dependencies

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Created with ❤️ by [Your Name] - April 2025


