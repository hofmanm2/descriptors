import logging
from io import StringIO
from decorators import safe_import

def main():
    # Set up logging
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger = logging.getLogger('demo_logger')
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
        
    # 1. Basic module import
    print("1. Basic module import:")
    math = safe_import('math')
    if math:
        print(f"   Success! math.sqrt(16) = {math.sqrt(16)}")
    print()
    
    # 2. Import with alias
    print("2. Import with alias:")
    np = safe_import('math', alias='np')  # Using math as np for demo
    if np:
        print(f"   Success! np.pi = {np.pi}")
    print()
    
    # 3. Handling non-existent module
    print("3. Handling non-existent module:")
    nonexistent = safe_import('nonexistent_module', logger=logger)
    print(f"   Result: {nonexistent}")
    print(f"   Log output: {stream.getvalue().strip()}")
    stream.truncate(0)
    stream.seek(0)
    print()
    
    # 4. Custom globals dictionary
    print("4. Custom globals dictionary:")
    custom_globals = {}
    safe_import('datetime', globals_dict=custom_globals)
    print(f"   Module keys in custom_globals: {list(custom_globals.keys())}")
    print(f"   datetime in main globals: {'datetime' in globals()}")
    print(f"   Current date: {custom_globals['datetime'].date.today()}")
    print()
    
    # 5. Prevent overwriting existing globals
    print("5. Prevent overwriting:")
    # Create a dummy variable with the same name as a module
    globals()['json'] = "Not the json module"
    print(f"   Before: json = {json}")
    
    # Try to import without overwriting
    safe_import('json', overwrite=False)
    print(f"   After import with overwrite=False: json = {json}")
    
    # Now allow overwriting
    json_module = safe_import('json', overwrite=True)
    print(f"   After import with overwrite=True: json is module? {isinstance(json_module, type(math))}")
    print(f"   json.dumps([1, 2, 3]): {json.dumps([1, 2, 3])}")
    print()
    
    # 6. Nested submodule import
    print("6. Nested submodule import:")
    xml_etree = safe_import('xml.etree.ElementTree')
    if xml_etree:
        root = xml_etree.Element('root')
        child = xml_etree.SubElement(root, 'child')
        child.text = "Hello, World!"
        print(f"   Successfully imported xml.etree.ElementTree")
        print(f"   'xml' also available in globals: {'xml' in globals()}")
        print(f"   Created XML: {xml_etree.tostring(root).decode()}")
    print()
    
    # 7. Combined features
    print("7. Combined features (alias + custom globals):")
    new_globals = {}
    dt = safe_import('datetime', alias='dt', globals_dict=new_globals)
    print(f"   Keys in new_globals: {list(new_globals.keys())}")
    print(f"   Current time: {new_globals['dt'].datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()