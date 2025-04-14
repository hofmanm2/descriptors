import unittest
import logging
from io import StringIO
import datetime

from decorators import safe_catch, SafeCatchContextManager, ExceptionInfo


class TestSafeCatch(unittest.TestCase):
    def setUp(self):
        # Set up a logger that writes to a StringIO buffer for testing
        self.log_buffer = StringIO()
        self.handler = logging.StreamHandler(self.log_buffer)
        self.handler.setFormatter(logging.Formatter('%(levelname)s:%(message)s'))
        
        self.logger = logging.getLogger('test_logger')
        self.logger.setLevel(logging.DEBUG)  # Capture all levels
        self.logger.addHandler(self.handler)
        self.logger.propagate = False  # Don't propagate to parent loggers
        
        # Clear the global exception list before each test
        SafeCatchContextManager.clear_global_exceptions()
        
    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.handler.close()
    
    def test_exception_info_class(self):
        """Test the ExceptionInfo class functionality."""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            info = ExceptionInfo(type(e), e, e.__traceback__, "test context")
            
            # Check all attributes are properly set
            self.assertEqual(info.exc_type, ValueError)
            self.assertEqual(str(info.exc_val), "Test exception")
            self.assertIsNotNone(info.exc_tb)
            self.assertEqual(info.context, "test context")
            self.assertIsInstance(info.timestamp, datetime.datetime)
            self.assertIn("ValueError: Test exception", info.traceback_str)
            
            # Check string representation
            self.assertIn("test context - ValueError: Test exception", str(info))
    
    def test_normal_function_execution(self):
        """Test that the decorator allows normal function execution."""
        @safe_catch(logger=self.logger)
        def normal_function(x, y):
            return x + y
        
        result = normal_function(2, 3)
        self.assertEqual(result, 5)
        self.assertEqual(self.log_buffer.getvalue(), "")  # No logs should be generated
        self.assertEqual(len(normal_function.__self__.get_exceptions()), 0)  # No exceptions stored
    
    def test_exception_tracking_in_function(self):
        """Test that exceptions are tracked when using the decorator."""
        @safe_catch(logger=self.logger)
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        self.assertIsNone(result)  # Should return None when exception is caught
        
        # Check the exception was stored
        exceptions = failing_function.__self__.get_exceptions()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0].exc_type, ValueError)
        self.assertEqual(str(exceptions[0].exc_val), "Test error")
        self.assertIn("failing_function()", exceptions[0].context)
        
        # Check log output
        log_output = self.log_buffer.getvalue()
        self.assertIn("ERROR:An error occurred: Test error", log_output)
    
    def test_global_exception_tracking(self):
        """Test that exceptions can be tracked globally."""
        @safe_catch(track_globally=True, logger=self.logger)
        def failing_function():
            raise ValueError("Global tracking test")
        
        failing_function()
        
        # Check instance tracking
        exceptions = failing_function.__self__.get_exceptions()
        self.assertEqual(len(exceptions), 1)
        
        # Check global tracking
        global_exceptions = SafeCatchContextManager.get_global_exceptions()
        self.assertEqual(len(global_exceptions), 1)
        self.assertEqual(str(global_exceptions[0].exc_val), "Global tracking test")
        
        # Clear instance exceptions and check global still exists
        failing_function.__self__.clear_exceptions()
        self.assertEqual(len(failing_function.__self__.get_exceptions()), 0)
        self.assertEqual(len(SafeCatchContextManager.get_global_exceptions()), 1)
        
        # Clear global exceptions
        SafeCatchContextManager.clear_global_exceptions()
        self.assertEqual(len(SafeCatchContextManager.get_global_exceptions()), 0)
    
    def test_context_manager_exception_tracking(self):
        """Test exception tracking in context manager."""
        with safe_catch(logger=self.logger) as catcher:
            raise ValueError("Context error")
        
        # Check the exception was stored
        exceptions = catcher.get_exceptions()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0].exc_type, ValueError)
        self.assertEqual(str(exceptions[0].exc_val), "Context error")
        self.assertEqual(exceptions[0].context, "context_manager")
        
        # Check log output
        log_output = self.log_buffer.getvalue()
        self.assertIn("ERROR:An error occurred: Context error", log_output)
    
    def test_multiple_exceptions(self):
        """Test tracking multiple exceptions."""
        # Use global tracking for this test
        with safe_catch(logger=self.logger, track_globally=True) as catcher:
            try:
                raise ValueError("First error")
            except ValueError:
                pass  # Catch but don't suppress with safe_catch
            
            # Now raise an exception that safe_catch will handle
            raise RuntimeError("Second error")
        
        # Only the second exception should be tracked locally
        exceptions = catcher.get_exceptions()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0].exc_type, RuntimeError)
        
        # Create a function with controlled exception raising and global tracking
        @safe_catch(logger=self.logger, track_globally=True)
        def failing_multiple():
            # Raise exception - will be caught by decorator
            raise ValueError("Function exception")
        
        # Raise and catch an exception
        failing_multiple()
        
        # Test global exception tracking
        global_tracker = SafeCatchContextManager.get_global_exceptions()
        self.assertEqual(len(global_tracker), 2)  # Should have exactly 2 globally tracked exceptions
        
        # Verify we have the expected exceptions
        exception_messages = [str(exc.exc_val) for exc in global_tracker]
        self.assertIn("Second error", exception_messages)
        self.assertIn("Function exception", exception_messages)
    
    def test_class_decorator_exception_tracking(self):
        """Test exception tracking when used as a class decorator."""
        @safe_catch(logger=self.logger)
        class TestClass:
            def method_works(self):
                return "success"
                
            def method_fails(self):
                raise ValueError("Method error")
        
        obj = TestClass()
        
        # Test normal method works
        self.assertEqual(obj.method_works(), "success")
        
        # Test failing method is handled and exception is tracked
        result = obj.method_fails()
        self.assertIsNone(result)
        
        # Check that we can access exception history through the class
        # Use the __context_manager__ attribute we added
        exceptions = obj.__class__.__context_manager__.get_exceptions()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0].exc_type, ValueError)
        self.assertIn("method_fails", exceptions[0].context)
        
        log_output = self.log_buffer.getvalue()
        self.assertIn("ERROR:An error occurred: Method error", log_output)
    
    def test_context_reraise_exception(self):
        """Test that context manager can re-raise exceptions but still track them."""
        with self.assertRaises(RuntimeError):
            with safe_catch(suppress=False, logger=self.logger) as catcher:
                raise RuntimeError("Should propagate")
        
        # Even though we re-raised, we should still track the exception
        exceptions = catcher.get_exceptions()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0].exc_type, RuntimeError)
        self.assertEqual(str(exceptions[0].exc_val), "Should propagate")
        
        # Check we logged at debug level but not error level
        log_output = self.log_buffer.getvalue()
        self.assertIn("DEBUG:Not suppressing exception", log_output)
        self.assertNotIn("ERROR:", log_output)
    
    def test_function_arguments_in_context(self):
        """Test that function arguments are captured in the context."""
        @safe_catch(logger=self.logger)
        def func_with_args(a, b, c=None):
            raise ValueError(f"Error with {a}, {b}, {c}")
        
        func_with_args(1, "test", c={"key": "value"})
        
        exceptions = func_with_args.__self__.get_exceptions()
        self.assertEqual(len(exceptions), 1)
        
        # Check that args and kwargs are in the context
        self.assertIn("func_with_args", exceptions[0].context)
        self.assertIn("1", exceptions[0].context)
        self.assertIn("test", exceptions[0].context)
        self.assertIn("key", exceptions[0].context)
    
    def test_traceback_capture(self):
        """Test that tracebacks are properly captured."""
        def nested_function():
            raise ValueError("Nested error")
            
        @safe_catch(logger=self.logger)
        def outer_function():
            nested_function()
        
        outer_function()
        
        exceptions = outer_function.__self__.get_exceptions()
        self.assertEqual(len(exceptions), 1)
        
        # Check traceback contains both function names
        self.assertIn("nested_function", exceptions[0].traceback_str)
        self.assertIn("outer_function", exceptions[0].traceback_str)


if __name__ == '__main__':
    unittest.main()