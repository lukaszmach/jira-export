import os
import sys

# Add the parent directory of 'tests' to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import jira_export.jira_export as j