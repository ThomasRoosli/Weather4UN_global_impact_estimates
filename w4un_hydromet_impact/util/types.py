"""
Definitions for frequently used type aliases.
"""
from typing import Literal

import numpy as np

# Type definition for a 1-dimensional array of floats
FloatingArray = np.ndarray[Literal[1], np.dtype[np.floating]]
# Type definition for a 1-dimensional array of integers
IntegerArray = np.ndarray[Literal[1], np.dtype[np.signedinteger]]
# Type definition for a 1-dimensional array of strings
StringArray = np.ndarray[Literal[1], np.dtype[np.str_]]

# Type definition for timestamps used in C4M
Timestamp = np.datetime64
# Type definition for a 1-dimensional array of timestamps
TimestampArray = np.ndarray[Literal[1], np.dtype[Timestamp]]
