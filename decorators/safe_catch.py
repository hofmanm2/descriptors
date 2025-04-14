import logging
import functools
import types
import datetime
import traceback
from typing import Optional, Any, TypeVar, Callable, Type, Union, List


T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])
C = TypeVar('C', bound=Type[Any])

class ExceptionInfo:
    """Container for exception information."""
    
    def __init__(self, 
                 exc_type: Type[BaseException], 
                 exc_val: BaseException,
                 exc_tb: Optional[types.TracebackType] = None,
                 context: str = ""):
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.exc_tb = exc_tb
        self.context = context
        self.timestamp = datetime.datetime.now()
        self.traceback_str = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))
    
    def __str__(self) -> str:
        return f"{self.timestamp}: {self.context} - {self.exc_type.__name__}: {self.exc_val}"
    
    def __repr__(self) -> str:
        return self.__str__()

# Global registry for exception tracking
class ExceptionRegistry:
    """Global registry for exception tracking across decorators."""
    _global_exceptions: List[ExceptionInfo] = []
    
    @classmethod
    def add_exception(cls, exception_info: ExceptionInfo) -> None:
        cls._global_exceptions.append(exception_info)
    
    @classmethod
    def get_exceptions(cls) -> List[ExceptionInfo]:
        return cls._global_exceptions
    
    @classmethod
    def clear_exceptions(cls) -> None:
        cls._global_exceptions.clear()

# Default logging setup
def get_default_logger(name: str = None) -> logging.Logger:
    """Get a default logger if none is provided."""
    return logging.getLogger(name or __name__)

class SafeCatchContextManager:
    """Context manager for catching exceptions."""
    
    def __init__(self, suppress: bool = True, 
                 message: str = "An error occurred",
                 logger: Optional[logging.Logger] = None,
                 track_globally: bool = False):
        self.suppress = suppress
        self.message = message
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.track_globally = track_globally
        self.exceptions: List[ExceptionInfo] = []
    
    def __enter__(self) -> 'SafeCatchContextManager':
        return self
    
    def __exit__(self, 
                exc_type: Optional[Type[BaseException]], 
                exc_val: Optional[BaseException],
                exc_tb: Optional[types.TracebackType]) -> bool:
        if exc_type is not None:
            # Store the exception information
            self._store_exception(exc_type, exc_val, exc_tb, "context_manager")
            
            if self.suppress:
                self.logger.error(f"{self.message}: {exc_val}")
                return True  # Suppress the exception
            self.logger.debug(f"Not suppressing exception: {exc_val}")
            return False  # Re-raise the exception
        return False
        
    def __call__(self, func_or_class: Union[F, C]) -> Union[F, C]:
        """Make SafeCatchContextManager callable so it can be used as a decorator."""
        if isinstance(func_or_class, type):  # If decorating a class
            return self._decorate_class(func_or_class)
        else:  # If decorating a function
            return self._decorate_function(func_or_class)
    
    def _decorate_function(self, func: F) -> F:
        """Decorate a function with exception handling."""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get the exception details
                exc_type = type(e)
                exc_val = e
                exc_tb = e.__traceback__
                
                # Format the context string more cleanly
                # Create a prettier representation of the function call
                if not args and not kwargs:
                    context = f"{func.__name__}()"
                else:
                    args_str = ", ".join([repr(arg) for arg in args]) if args else ""
                    kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()]) if kwargs else ""
                    
                    # Add comma between args and kwargs if both exist
                    separator = ", " if args_str and kwargs_str else ""
                    context = f"{func.__name__}({args_str}{separator}{kwargs_str})"
                
                self._store_exception(exc_type, exc_val, exc_tb, context)
                
                if self.suppress:
                    self.logger.error(f"{self.message}: {e}")
                    return None
                else:
                    self.logger.debug(f"Re-raising exception: {e}")
                    raise  
        
        # Add reference to self on the wrapper function
        # This allows tests to access exceptions through the decorated function
        wrapper.__self__ = self
        
        return wrapper  # type: ignore
    
    def _decorate_class(self, cls: C) -> C:
        """Decorate a class by wrapping its methods with exception handling."""
        # Store the context manager on the class for easier access
        cls.__context_manager__ = self
        
        for attr_name, attr_value in cls.__dict__.items():
            # Skip special methods and non-callable attributes
            if attr_name.startswith('__') or not callable(attr_value):
                continue
            
            decorated_method = self._decorate_function(attr_value)
            # Each decorated method needs access to the context manager
            setattr(cls, attr_name, decorated_method)
        
        return cls
    
    def _store_exception(self, 
                         exc_type: Type[BaseException], 
                         exc_val: BaseException,
                         exc_tb: Optional[types.TracebackType], 
                         context: str) -> None:
        """Store exception information."""
        exception_info = ExceptionInfo(exc_type, exc_val, exc_tb, context)
        self.exceptions.append(exception_info)
        
        if self.track_globally:
            ExceptionRegistry.add_exception(exception_info)
    
    def get_exceptions(self) -> List[ExceptionInfo]:
        """Get list of caught exceptions."""
        return self.exceptions
    
    def clear_exceptions(self) -> None:
        """Clear the list of caught exceptions."""
        self.exceptions.clear()
    
    @classmethod
    def get_global_exceptions(cls) -> List[ExceptionInfo]:
        """Get all exceptions caught by any instance."""
        return ExceptionRegistry.get_exceptions()
    
    @classmethod
    def clear_global_exceptions(cls) -> None:
        """Clear all globally tracked exceptions."""
        ExceptionRegistry.clear_exceptions()


def safe_catch(
    func_or_suppress: Any = True,
    message: str = "An error occurred",
    logger: Optional[logging.Logger] = None,
    suppress: bool = True,
    track_globally: bool = False
) -> Any:
    """
    Context Decorator that catches exceptions, logs them, and stores history for later analysis.
    
    Can be used in various ways:
    
    - simple decorator:
       @safe_catch
       def my_function():
           ...
    
    - parameterized decorator:
       @safe_catch(message="Custom message")
       def my_function():
           ...
    
    - class decorator:
       @safe_catch(message="Error in class")
       class MyClass:
           ...
    
    -  context manager:
       with safe_catch(message="Custom message") as catcher:
           # code that might raise exceptions            
           ...
       exceptions = catcher.get_exceptions()
       
    Args:
        func_or_suppress: Either the function to decorate or the suppress flag.
        suppress (bool): If True, suppress the exception and log it.
        message (str): Custom message to log with the exception.
        logger (logging.Logger, optional): Custom logger to use. If None, uses the root logger.
        track_globally (bool): If True, also store exceptions in global registry.
    
    Returns:
        Either a decorated function/class or a context manager.
    """
    # Check if used directly as a decorator
    if callable(func_or_suppress) and not isinstance(func_or_suppress, bool):
        func = func_or_suppress
        if logger is None:
            logger = logging.getLogger(__name__)

        # Create a context manager for the function
        context_manager = SafeCatchContextManager(suppress, message, logger, track_globally)
        return context_manager(func)

    # Create a context that can also serve as a decorator
    context = SafeCatchContextManager(suppress, message, logger, track_globally)
    return context