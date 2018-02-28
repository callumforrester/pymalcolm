from malcolm.modules.ADCore.parts import DetectorDriverPart
from malcolm.modules.ADCore.infos import NDArrayDatasetInfo
from malcolm.modules.scanning.controllers import RunnableController


class Andor3DriverPart(DetectorDriverPart):
    @RunnableController.ReportStatus
    def report_configuration(self, context):
        infos = super(Andor3DriverPart, self).report_configuration(
            context) + [NDArrayDatasetInfo(rank=2)]
        return infos

    def setup_detector(self, child, completed_steps, steps_to_do, params=None):
        fs = super(Andor3DriverPart, self).setup_detector(
            child, completed_steps, steps_to_do, params)

        duration = params.generator.duration
        readout_time = child.readoutTime.value
        exposure = duration - readout_time
        fs.append(child.exposure.put_value_async(exposure))
        child.wait_all_futures(fs)

        # Need to reset acquirePeriod as it's sometimes wrong
        fs = child.acquirePeriod.put_value_async(exposure + readout_time)

        return fs
