import importlib.util
import warnings

# Patch pytesseract to use importlib.util.find_spec instead of pkgutil.find_loader
def patch_pytesseract():
    try:
        import pytesseract
        
        # Replace the deprecated find_loader calls
        def check_numpy():
            return importlib.util.find_spec('numpy') is not None
            
        def check_pandas():
            return importlib.util.find_spec('pandas') is not None
        
        # Apply the patches
        pytesseract.numpy_installed = check_numpy()
        pytesseract.pandas_installed = check_pandas()
        
        return True
    except ImportError:
        return False

# Patch PyPDF2 warning
def patch_pypdf2():
    try:
        # Just suppress the warning
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning, 
                               message="PyPDF2 is deprecated")
        return True
    except ImportError:
        return False

# Patch reportlab warning
def patch_reportlab():
    try:
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning, 
                               message="ast.NameConstant is deprecated")
        return True
    except ImportError:
        return False

def apply_all_patches():
    """Apply all patches to fix dependency warnings"""
    patch_pytesseract()
    patch_pypdf2()
    patch_reportlab() 