import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import setup_malcolm_paths

import unittest
from mock import MagicMock, call
from time import sleep

# logging
# import logging
# logging.basicConfig(level=logging.DEBUG)

# module imports
from malcolm.controllers.managercontroller import ManagerController
from malcolm.core import method_writeable_in, method_takes, DefaultStateMachine
from malcolm.core import Process, Part, Table
from malcolm.core.syncfactory import SyncFactory
from malcolm.parts.builtin.childpart import ChildPart


class TestManagerController(unittest.TestCase):

    def checkState(self, state, child=True, parent=True):
        if child:
            self.assertEqual(self.c_child.state.value, state)
        if parent:
            self.assertEqual(self.c.state.value, state)

    def setUp(self):
        self.s = SyncFactory('threading')
        self.p = Process('process1', self.s)

        # create a child ManagerController block
        params = ManagerController.MethodMeta.\
            prepare_input_map(mri='childBlock')
        self.c_child = ManagerController(self.p, [], params)
        self.b_child = self.c_child.block

        self.sm = self.c_child.stateMachine

        params = Part.MethodMeta.prepare_input_map(name='part1')
        part1 = Part(self.p, params)
        params = {'name': 'part2', 'mri': 'childBlock'}
        params = ChildPart.MethodMeta.prepare_input_map(**params)
        part2 = ChildPart(self.p, params)

        # create a root block for the ManagerController block to reside in
        parts = [part1, part2]
        params = {'mri': 'mainBlock'}
        params = ManagerController.MethodMeta.prepare_input_map(**params)
        self.c = ManagerController(self.p, parts, params)
        self.b = self.c.block

        # check that do_initial_reset works asynchronously
        self.checkState(self.sm.DISABLED)
        self.p.start()

        retry = 0
        while retry < 20 and self.c.state.value != self.sm.READY:
            sleep(.1)
            retry += 1
        self.checkState(self.sm.READY)

    def test_init(self):

        # the following block attributes should be created by a call to
        # set_attributes via _set_block_children in __init__
        self.assertEqual(self.b['layout'].meta.typeid,
                         'malcolm:core/TableMeta:1.0')
        self.assertEqual(self.b['layoutName'].meta.typeid,
                         'malcolm:core/StringMeta:1.0')

        # the following hooks should be created via _find_hooks in __init__
        self.assertEqual(self.c.hook_names, {
            self.c.Reset: "Reset",
            self.c.Disable: "Disable",
            self.c.Layout: "Layout",
            self.c.ReportOutports: "ReportOutports",
            self.c.Load: "Load",
            self.c.Save: "Save",
        })

        # check instantiation of object tree via logger names
        self.assertEqual(self.c._logger.name,
                         'ManagerController(mainBlock)')
        self.assertEqual(self.c.parts['part1']._logger.name,
                         'ManagerController(mainBlock).part1')
        self.assertEqual(self.c.parts['part2']._logger.name,
                         'ManagerController(mainBlock).part2')
        self.assertEqual(self.c_child._logger.name,
                         'ManagerController(childBlock)')

    def test_edit(self):
        self.c.edit()
        # editing only affects one level
        self.checkState(self.sm.EDITABLE, child=False)
        self.assertEqual(self.c.revert_structure, self.c._save_to_structure())

    def test_edit_exception(self):
        self.c.edit()
        with self.assertRaises(Exception):
            self.c.edit()

    def test_save(self):
        self.c.edit()
        params = {'layoutName': 'testSaveLayout'}
        params = ManagerController.save.MethodMeta.prepare_input_map(**params)
        self.c.save(params)
        self.checkState(self.sm.AFTER_RESETTING, child=False)
        self.assertEqual(self.c.layout_name.value, 'testSaveLayout')

    def test_revert(self):
        self.c.edit()
        self.c.revert()
        self.checkState(self.sm.AFTER_RESETTING, child=False)

    def test_load_layout(self):
        self.c.edit()
        self.checkState(self.sm.EDITABLE, child=False)
        # self.b.layoutName = 'testSaveLayout'
        new_layout = Table(self.c.layout.meta)
        new_layout.name = ["part2"]
        new_layout.mri = ["P45-MRI"]
        new_layout.x = [10]
        new_layout.y = [20]
        new_layout.visible = [True]
        self.b.layout = new_layout
        self.assertEqual(self.c.parts['part2'].x, 10)
        self.assertEqual(self.c.parts['part2'].y, 20)
        self.assertEqual(self.c.parts['part2'].visible, True)

if __name__ == "__main__":
    unittest.main(verbosity=2)