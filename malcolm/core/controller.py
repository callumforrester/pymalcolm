import inspect
import weakref

from malcolm.compat import OrderedDict
from .attribute import Attribute
from .attributemodel import AttributeModel
from .block import Block
from .blockmeta import BlockMeta
from .blockmodel import BlockModel
from .context import Context
from .errors import UnexpectedError, AbortedError
from .healthmeta import HealthMeta
from .hook import Hook, get_hook_decorated
from .loggable import Loggable
from .map import Map
from .method import Method
from .methodmodel import MethodModel, get_method_decorated
from .model import Model
from .notifier import Notifier
from .request import Get, Subscribe, Unsubscribe, Put, Post
from .queue import Queue
from .rlock import RLock
from .serializable import serialize_object
from .view import make_view


class Controller(Loggable):
    use_cothread = True

    # Attributes
    health = None

    def __init__(self, process, mri, parts, publish=True):
        self.set_logger_name("%s(%s)" % (type(self).__name__, mri))
        self.process = process
        self.mri = mri
        # {Part: fault string}
        self._faults = {}
        # {Hook: name}
        self._hook_names = self._find_hooks()
        # {name: Part}
        self._parts = self._setup_parts(parts)
        self._lock = RLock()
        self._block = BlockModel()
        self._notifier = Notifier(mri, self._lock, self._block)
        self._block.set_notifier_path(self._notifier, [])
        self._write_functions = {}
        self._add_block_fields([self.create_meta()])
        self._add_block_fields(self.create_attributes())
        self._add_block_fields(self.create_methods())
        self._add_block_fields(self.create_part_fields())
        process.add_controller(mri, self, publish)

    def _setup_parts(self, parts):
        parts_dict = OrderedDict()
        for part in parts:
            part.attach_to_controller(self)
            # Check part hooks into one of our hooks
            for func_name, part_hook, _ in get_hook_decorated(part):
                assert part_hook in self._hook_names, \
                    "Part %s func %s not hooked into %s" % (
                        part.name, func_name, self)
            parts_dict[part.name] = part
        return parts_dict

    def _find_hooks(self):
        hook_names = {}
        for name, member in inspect.getmembers(self, Hook.isinstance):
            assert member not in hook_names, \
                "Hook %s already in %s as %s" % (self, name, hook_names[member])
            hook_names[member] = name
        return hook_names

    def _add_block_fields(self, fields):
        for name, child, writeable_func in fields:
            self._block.set_endpoint_data(name, child)
            self._write_functions[name] = writeable_func

    def create_methods(self):
        """Method that should provide Method instances for Block

        Yields:
            tuple: (string name, Method, callable post_function).
        """
        return get_method_decorated(self)

    def create_attributes(self):
        """MethodModel that should provide Attribute instances for Block

        Yields:
            tuple: (string name, Attribute, callable put_function).
        """
        self.health = HealthMeta().make_attribute()
        yield "health", self.health, None

    def create_meta(self):
        """Create the Block meta object"""
        return "meta", BlockMeta(), None

    def create_part_fields(self):
        for part in self._parts.values():
            for data in part.create_attributes():
                yield data
            for data in part.create_methods():
                yield data

    def spawn(self, func, *args, **kwargs):
        """Spawn a function in the right thread"""
        spawned = self.process.spawn(func, args, kwargs, self.use_cothread)
        return spawned

    @property
    def changes_squashed(self):
        return self._notifier.changes_squashed

    def set_health(self, part, alarm=None):
        """Set the health attribute"""
        with self.changes_squashed:
            if alarm is None:
                self._faults.pop(part, None)
            else:
                self._faults[part] = alarm
            if self._faults:
                # Sort them by severity
                faults = sorted(self._faults.values(), key=lambda a: a.severity)
                alarm = faults[-1]
                text = faults[-1].message
            else:
                alarm = None
                text = "OK"
            self.health.set_value(text)
            self.health.set_alarm(alarm)
            self.health.set_timeStamp()

    def make_view(self, context, data=None, child_name=None):
        """Make a child View of data[child_name]"""
        with self._lock:
            if data is None:
                child = self._block
            else:
                child = data[child_name]
            child_view = self._make_view(context, child)
        return child_view

    def _make_view(self, context, data):
        if isinstance(data, BlockModel):
            # Make an Attribute View
            return make_view(self, context, data, Block)
        elif isinstance(data, AttributeModel):
            # Make an Attribute View
            return make_view(self, context, data, Attribute)
        elif isinstance(data, MethodModel):
            # Make a Method View
            return make_view(self, context, data, Method)
        elif isinstance(data, Model):
            # Make a view of it
            return make_view(self, context, data)
        elif isinstance(data, dict):
            # Need to recurse down
            d = OrderedDict()
            for k, v in data.items():
                d[k] = self._make_view(context, v)
            return d
        elif isinstance(data, list):
            # Need to recurse down
            return [self._make_view(context, x) for x in data]
        else:
            return data

    def handle_request(self, request):
        """Spawn a new thread that handles Request"""
        if isinstance(request, Get):
            handler = self._handle_get
        elif isinstance(request, Put):
            handler = self._handle_put
        elif isinstance(request, Post):
            handler = self._handle_post
        elif isinstance(request, Subscribe):
            handler = self._notifier.handle_subscribe
        elif isinstance(request, Unsubscribe):
            handler = self._notifier.handle_unsubscribe
        else:
            raise UnexpectedError("Unexpected request %s", request)
        return self.spawn(self._run_handler, handler, request)

    def _run_handler(self, handler, request):
        try:
            handler(request)
        except Exception as e:
            self.log_exception("Exception when handling %s", request)
            request.respond_with_error(str(e))

    def _handle_get(self, request):
        with self._lock:
            data = self._block
            for endpoint in request.path[1:]:
                data = data[endpoint]
            serialized = serialize_object(data)
        request.respond_with_return(serialized)

    def _handle_put(self, request):
        attribute_name = request.path[1]

        with self._lock:
            attribute = self._block[attribute_name]
            assert attribute.meta.writeable, \
                "Attribute %s is not writeable" % attribute_name
            put_function = self._write_functions[attribute_name]

        result = put_function(request.value)
        request.respond_with_return(result)

    def _handle_post(self, request):
        method_name = request.path[1]
        if request.parameters:
            param_dict = request.parameters
        else:
            param_dict = {}

        with self._lock:
            method = self._block[method_name]
            assert method.writeable, \
                "Method %s is not writeable" % method_name
            args = method.prepare_call_args(**param_dict)
            post_function = self._write_functions[method_name]

        result = post_function(*args)
        result = self.validate_result(method_name, result)
        request.respond_with_return(result)

    def validate_result(self, method_name, result):
        with self._lock:
            method = self._block[method_name]
            # Prepare output map
            if method.returns.elements:
                result = Map(method.returns, result)
                result.check_valid()
        return result

    def create_part_contexts(self):
        part_contexts = {}
        for part_name, part in self._parts.items():
            part_contexts[part] = Context(
                "Context(%s)" % part_name, self.process)
        return part_contexts

    def run_hook(self, hook, part_contexts, *args, **params):
        hook_queue, hook_runners = self.start_hook(
            hook, part_contexts, *args, **params)
        return_dict = self.wait_hook(hook_queue, hook_runners)
        return return_dict

    def start_hook(self, hook, part_contexts, *args, **params):
        assert hook in self._hook_names, \
            "Hook %s doesn't appear in controller hooks %s" % (
                hook, self._hook_names)

        # This queue will hold (part, result) tuples
        hook_queue = Queue()

        # ask the hook to find the functions it should run
        part_funcs = hook.find_hooked_functions(self._parts.values())
        hook_runners = {}

        # now start them off
        for part, func_name in part_funcs.items():
            context = part_contexts[part]
            hook_runners[part] = part.make_hook_runner(
                hook_queue, func_name, weakref.proxy(context), *args, **params)

        return hook_queue, hook_runners

    def wait_hook(self, hook_queue, hook_runners):
        # Wait for them all to finish
        return_dict = {}
        while hook_runners:
            part, ret = hook_queue.get()
            hook_runner = hook_runners.pop(part)

            if isinstance(ret, AbortedError):
                # If AbortedError, all tasks have already been stopped.
                # Do not wait on them otherwise we might get a deadlock...
                raise ret

            # Wait for the process to terminate
            hook_runner.wait()
            return_dict[part.name] = ret
            self.log_debug("Part %s returned %r. Still waiting for %s",
                           part.name, ret, [p.name for p in hook_runners])

            if isinstance(ret, Exception):
                # Got an error, so stop and wait all hook runners
                for h in hook_runners.values():
                    h.stop()
                # Wait for them to finish
                for h in hook_runners.values():
                    h.wait()
                raise ret

        return return_dict
