from mock import MagicMock, ANY, call

from scanpointgenerator import LineGenerator, CompoundGenerator
from malcolm.core import call_with_params, Context, Process
from malcolm.modules.ADAndor3.parts import Andor3DriverPart
from malcolm.modules.ADAndor3.blocks import andor3_detector_driver_block
from malcolm.testutil import ChildTestCase
from numpy import float64


class TestAndor3DetectorDriverPart(ChildTestCase):

    def setUp(self):
        self.process = Process("Process")
        self.context = Context(self.process)
        self.child = self.create_child_block(
            andor3_detector_driver_block, self.process,
            mri="mri", prefix="prefix")
        choices = ["Fixed", "Continuous"]
        self.child.parts["imageMode"].attr.meta.set_choices(choices)
        self.o = call_with_params(
            Andor3DriverPart, name="m", mri="mri")
        list(self.o.create_attribute_models())
        self.process.start()

    def tearDown(self):
        del self.context
        self.process.stop(timeout=1)

    def test_configure_with_rolling_shutter(self):
        # Need a known value for the readout time, array height and
        # shutter mode
        self.child.parts["readoutTime"].attr.set_value(0.002)
        self.child.parts["arrayHeight"].attr.set_value(270)
        choices = ["Rolling", "Global"]
        self.child.parts["shutterMode"].attr.meta.set_choices(choices)
        self.child.parts["shutterMode"].attr.set_value("Rolling")

        self.do_test_configure([
            call.put('arrayCallbacks', True),
            call.put('arrayCounter', 0),
            call.put('numImages', 6000000),
            call.put('exposure', 0.09799259259259259),
            call.put('acquirePeriod', 0.09999259259259259),
            call.post('start')])

    def test_configure_with_global_shutter(self):
        self.child.parts["readoutTime"].attr.set_value(0.002)
        self.child.parts["arrayHeight"].attr.set_value(270)
        choices = ["Rolling", "Global"]
        self.child.parts["shutterMode"].attr.meta.set_choices(choices)
        self.child.parts["shutterMode"].attr.set_value("Global")

        self.do_test_configure([
            call.put('arrayCallbacks', True),
            call.put('arrayCounter', 0),
            call.put('numImages', 6000000),
            call.put('exposure', 0.09797037037037037),
            call.put('acquirePeriod', 0.09997037037037038),
            call.post('start')])

    def do_test_configure(self, exptected_mock_calls):
        params = MagicMock()
        xs = LineGenerator("x", "mm", 0.0, 0.5, 3000, alternate=True)
        ys = LineGenerator("y", "mm", 0.0, 0.1, 2000)
        params.generator = CompoundGenerator([ys, xs], [], [], 0.1)
        params.generator.prepare()
        completed_steps = 0
        steps_to_do = 2000*3000
        part_info = ANY

        self.o.configure(
            self.context, completed_steps, steps_to_do, part_info, params)
        # Need to wait for the spawned mock start call to run
        self.o.start_future.result()
        assert self.child.handled_requests.mock_calls == exptected_mock_calls
