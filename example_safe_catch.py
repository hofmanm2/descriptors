import logging
import datetime
import random
from decorators.safe_catch import safe_catch, ExceptionRegistry

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('safe_catch_demo')

# 1. Basic usage - Simple decorator with default settings
@safe_catch
def divide(a, b):
    """Basic function with potential division by zero error."""
    print(f"Attempting to divide {a} by {b}")
    return a / b

print("1. Basic decorator usage (suppresses exceptions):")
result = divide(10, 2)
print(f"   Result of divide(10, 2): {result}")
result = divide(10, 0)
print(f"   Result of divide(10, 0): {result}")
print()

# 2. Parameterized decorator
@safe_catch(message="Division error occurred", suppress=True, track_globally=True)
def advanced_divide(a, b):
    """Function with custom error message and global tracking."""
    return a / b

print("2. Parameterized decorator with custom message:")
result = advanced_divide(10, 0)
print(f"   Result of advanced_divide(10, 0): {result}")
print()

# 3. Non-suppressing decorator (will re-raise exceptions)
@safe_catch(suppress=False, message="This exception will be re-raised")
def will_fail(text):
    """This function will fail and not suppress the exception."""
    return int(text)

print("3. Non-suppressing decorator (will re-raise exceptions):")
try:
    result = will_fail("not a number")
    print("   This line will not be reached")
except ValueError as e:
    print(f"   Caught re-raised exception: {e}")
print()

# 4. Class decorator example
@safe_catch(message="Error in Calculator class", track_globally=True)
class Calculator:
    """A class decorated with safe_catch."""
    
    def __init__(self, initial_value=0):
        self.value = initial_value
    
    def add(self, x):
        """Add a value."""
        self.value += x
        return self.value
    
    def divide_by(self, x):
        """Divide by a value (might raise ZeroDivisionError)."""
        self.value /= x
        return self.value
    
    @classmethod
    def create_with_value(cls, value):
        """Class method with potential errors."""
        if isinstance(value, str):
            value = int(value)  # Could raise ValueError
        return cls(value)
    
    @staticmethod
    @safe_catch(message="Negative number provided to is_positive")
    def is_positive(number):
        """Static method with assertion."""
        assert number > 0, "Number must be positive"
        return True

print("4. Class decorator (applies to all methods):")
calc = Calculator(10)
print(f"   Initial value: {calc.value}")
print(f"   After adding 5: {calc.add(5)}")
print(f"   After dividing by 0: {calc.divide_by(0)}")
print(f"   Value after failed division: {calc.value}")

# Try the class and static methods
try:
    print(f"   Creating calculator with string: {Calculator.create_with_value('5')}")
    print(f"   Creating calculator with invalid string: {Calculator.create_with_value('abc')}")
except ValueError:
    print("   Class method failed despite decorator (shouldn't happen)")

print(f"   Is -5 positive: {Calculator.is_positive(-5)}")
print()

# 5. Context manager usage
print("5. Context manager usage:")
try:
    with safe_catch(message="Error in context") as catcher:
        print("   Inside context manager")
        raise ValueError("Intentional error in context")
    print("   After exception in context (execution continues)")
    
    # Access exceptions caught by this specific context manager
    exceptions = catcher.get_exceptions()
    print(f"   Number of exceptions caught: {len(exceptions)}")
    print(f"   First exception: {exceptions[0]}")
except Exception as e:
    print(f"   Context failed to catch exception: {e}")
print()

# 6. Accessing global exception registry
print("6. Accessing global exception registry:")
global_exceptions = ExceptionRegistry.get_exceptions()
print(f"   Total exceptions tracked globally: {len(global_exceptions)}")
print(f"   Last exception context: {global_exceptions[-1].context}")
print(f"   Exception type: {global_exceptions[-1].exc_type.__name__}")
print(f"   Exception message: {global_exceptions[-1].exc_val}")
print()

# 7. Multiple exceptions in a single function
@safe_catch(track_globally=True)
def unstable_function(iterations):
    """Function that might fail in several ways."""
    results = []
    for i in range(iterations):
        try:
            if i % 3 == 0:
                results.append(10 / 0)  # ZeroDivisionError
            elif i % 3 == 1:
                results.append(int("not_a_number"))  # ValueError
            else:
                results.append(random.randint(1, 10))
        except Exception:
            # This inner try-except won't prevent the decorator from working
            print(f"   Inner exception caught at iteration {i}")
            pass
    return results

print("7. Multiple potential exceptions:")
results = unstable_function(5)
print(f"   Results from unstable_function: {results}")
print()

# 8. Clear exception history
print("8. Clearing exception history:")
previous_count = len(ExceptionRegistry.get_exceptions())
print(f"   Exception count before clearing: {previous_count}")
ExceptionRegistry.clear_exceptions()
print(f"   Exception count after clearing: {len(ExceptionRegistry.get_exceptions())}")
print()

# 9. Demonstration of return values
print("9. Demonstration of return values when exceptions occur:")
@safe_catch
def returns_value():
    return "Success!"

@safe_catch
def returns_value_but_fails():
    raise RuntimeError("This function failed")
    return "This will never be returned"

print(f"   Function that succeeds: {returns_value()}")
print(f"   Function that fails: {returns_value_but_fails()}")
print()
