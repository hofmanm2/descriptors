import unittest
import logging
from types import ModuleType
from io import StringIO
import sys

from decorators import safe_import


class TestSafeImporter(unittest.TestCase):

    def setUp(self):
        # Clean up any leftover test imports
        for name in ('math', 'math_alias', 'json', 'testmod', 'xml', 'custom_import'):
            if name in globals():
                del globals()[name]
        
        # Set up a logger for testing
        self.log_buffer = StringIO()
        self.handler = logging.StreamHandler(self.log_buffer)
        self.handler.setFormatter(logging.Formatter('%(levelname)s:%(message)s'))
        
        self.logger = logging.getLogger('test_logger')
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.handler.close()

    def test_import_existing_module(self):
        mod = safe_import('math')
        self.assertIsInstance(mod, ModuleType)
        self.assertIn('math', globals())
        self.assertEqual(globals()['math'].sqrt(16), 4)

    def test_import_with_alias(self):
        mod = safe_import('math', alias='math_alias')
        self.assertIn('math_alias', globals())
        self.assertEqual(globals()['math_alias'].pi, mod.pi)

    def test_import_nonexistent_module(self):
        mod = safe_import('nonexistent_module_xyz', logger=self.logger)
        self.assertIsNone(mod)
        self.assertNotIn('nonexistent_module_xyz', globals())
        log_output = self.log_buffer.getvalue()
        self.assertIn("Error importing nonexistent_module_xyz", log_output)

    def test_prevent_overwrite(self):
        globals()['json'] = 'not a module'
        mod = safe_import('json', overwrite=False)
        self.assertEqual(globals()['json'], 'not a module')
        self.assertNotIsInstance(globals()['json'], ModuleType)

    def test_allow_overwrite(self):
        globals()['json'] = 'not a module'
        mod = safe_import('json', overwrite=True)
        self.assertIsInstance(mod, ModuleType)
        self.assertIsInstance(globals()['json'], ModuleType)

    def test_custom_globals_dict(self):
        """Test importing a module with a custom globals dictionary."""
        custom_globals = {}
        mod = safe_import('os', globals_dict=custom_globals)
        self.assertIsInstance(mod, ModuleType)
        self.assertIn('os', custom_globals)
        self.assertNotIn('os', globals())

    def test_nested_submodule(self):
        """Test importing a nested submodule."""
        mod = safe_import('xml.etree.ElementTree')
        self.assertIsInstance(mod, ModuleType)
        self.assertIn('xml', globals())
        self.assertTrue(hasattr(globals()['xml'].etree, 'ElementTree'))

    def test_custom_logger(self):
        """Test using a custom logger."""
        mod = safe_import('nonexistent_module_abc', logger=self.logger)
        self.assertIsNone(mod)
        log_output = self.log_buffer.getvalue()
        self.assertIn("Error importing nonexistent_module_abc", log_output)

    def test_reimport_module(self):
        """Test reimporting an already imported module."""
        # First import
        mod1 = safe_import('sys')
        self.assertIsInstance(mod1, ModuleType)
        
        # Remember the module id
        mod1_id = id(mod1)
        
        # Second import - should return the same module object
        mod2 = safe_import('sys')
        self.assertEqual(id(mod2), mod1_id)

    def test_combined_features(self):
        """Test using multiple features together: custom globals and alias."""
        custom_globals = {}
        mod = safe_import('datetime', alias='dt', globals_dict=custom_globals)
        self.assertIsInstance(mod, ModuleType)
        self.assertIn('dt', custom_globals)
        self.assertNotIn('dt', globals())
        self.assertNotIn('datetime', custom_globals)
        self.assertTrue(hasattr(custom_globals['dt'], 'datetime'))

    def test_syntax_error_in_import(self):
        """Test handling module that would raise a syntax error if imported."""
        # Create a temporary module with syntax error
        with open('syntax_error_module.py', 'w') as f:
            f.write("This is not valid Python syntax $#@!")
        
        try:
            # Add directory to path so the module can be found
            sys.path.insert(0, '.')
            
            # Try to import the module
            mod = safe_import('syntax_error_module', logger=self.logger)
            self.assertIsNone(mod)
            log_output = self.log_buffer.getvalue()
            self.assertIn("Error importing syntax_error_module", log_output)
        finally:
            # Clean up
            import os
            if os.path.exists('syntax_error_module.py'):
                os.remove('syntax_error_module.py')
            if 'syntax_error_module' in sys.modules:
                del sys.modules['syntax_error_module']
            sys.path.pop(0)


if __name__ == '__main__':
    unittest.main()
