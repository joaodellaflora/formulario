import sys
import importlib.util

print('python:', sys.executable)
spec = importlib.util.find_spec('pandas')
print('pandas spec:', spec)
