'''
Created on 17/02/2014

@author: aecker
'''
import sys, glob
#sys.path.append("C:\\WINDOWS\\WinSxS\\x86_Microsoft.VC90.CRT_1fc8b3b9a1e18e3b_9.0.30729.1_x-ww_6f74963e")
sys.path.append("C:\\WINDOWS\\WinSxS\\x86_microsoft.vc90.mfcloc_1fc8b3b9a1e18e3b_9.0.21022.8_none_b59bae9d65014b98")
#sys.path.append("C:\\Windows\\winsxs\\amd64_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.30729.1_none_99b61f5e8371c1d4")
# finally manually downloaded the MSVCP90.DLL and placed it into C:\Python27\lib\site-packages\Pythonwin\ for to fix the DLL not found error. 
# more paths on my VM (not tested):
# x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.21022.8_none_bcb86ed6ac711f91
# x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.30729.1_none_e163563597edeada
# x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.30729.4148_none_5090ab56bcba71c2
# x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.30729.4926_none_508ed732bcbc0e5a
# x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.30729.4940_none_50916076bcb9a742

from distutils.core import setup
import py2exe       # PyDev is wrong stating this as an unused import here - this import is needed by distutils/dist.py
# If run without args, build executables, in quiet mode.
if len(sys.argv) == 1:
    sys.argv.append("py2exe")

from app_const import APP_TITLE, APP_VERSION


setup(name = APP_TITLE,
      version = APP_VERSION,
      windows = [ dict(script = "ResOccMonitor.py") ], 
      options = dict(py2exe = dict(includes = [ "sip", "decimal" ], dll_excludes = ["oci.dll"])),
      data_files = [ ("", ["ResOccMonitor.cfg"]) ],
     )
