import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from pkg_resources import require
require("mock", "numpy", "tornado", "cothread", "ruamel.yaml",
        "scanpointgenerator")

from mock import MagicMock

try:
    import cothread
except:
    # cothread doesn't work on python3 at the moment
    cothread = MagicMock()
    # Tell Mock not to have a Method, otherwise we will be decorated
    del cothread.MethodMeta
    def callback_result(f, *args, **kwargs):
        return f(*args, **kwargs)
    cothread.CallbackResult.side_effect = callback_result
    sys.modules["cothread"] = cothread
    input_hook = MagicMock()
    sys.modules["cothread.input_hook"] = input_hook
    del input_hook.MethodMeta
catools = MagicMock()
# Tell Mock not to have a Method, otherwise we will be decorated
del catools.MethodMeta
cothread.catools = catools
