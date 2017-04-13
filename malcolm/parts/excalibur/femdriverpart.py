from malcolm.parts.builtin.childpart import ChildPart
from malcolm.controllers.scanning import RunnableController
from malcolm.infos.ADCore.ndarraydatasetinfo import NDArrayDatasetInfo


class FemDriverPart(ChildPart):
    # Only need to report that we will make a dataset, top level will do all
    # control
    @RunnableController.ReportStatus
    def report_configuration(self, _):
        return [NDArrayDatasetInfo(name=self.name, rank=2)]
