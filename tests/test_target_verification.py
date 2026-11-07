"""A valid route does not by itself establish a fair fixed-input comparison."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_target_run import verify_fixed_inputs


class FixedInputVerification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.baseline = ['vpr', 'arch.xml', 'case.blif', '--seed', '1', '--route_chan_width', '100',
                         '--device_width', '30', '--num_workers', '1', '--target_utilization', '0.1',
                         '--flat_routing', 'off', '--read_rr_graph', str(root / 'rr_graph.xml')]
        self.validation = list(self.baseline)
        for flag in ['--net_file', '--place_file']:
            for command, suffix in [(self.baseline, 'baseline'), (self.validation, 'candidate')]:
                file = root / (flag + suffix)
                file.write_text('same frozen input\n')
                command.extend([flag, str(file)])

    def test_identical_copies_pass(self):
        self.assertEqual(len(verify_fixed_inputs(self.baseline, self.validation)), 2)

    def test_changed_layout_fails(self):
        Path(self.validation[self.validation.index('--place_file') + 1]).write_text('different layout\n')
        with self.assertRaises(ValueError):
            verify_fixed_inputs(self.baseline, self.validation)

    def test_changed_constraints_and_rrg_fail(self):
        for flag in ['--seed', '--route_chan_width', '--device_width', '--num_workers', '--read_rr_graph']:
            with self.subTest(flag=flag):
                command = copy.copy(self.validation)
                command[command.index(flag) + 1] = 'different'
                with self.assertRaises(ValueError):
                    verify_fixed_inputs(self.baseline, command)

    def test_missing_or_duplicated_constraint_fails(self):
        command = list(self.validation)
        index = command.index('--seed')
        del command[index:index + 2]
        for bad in [command, self.validation + ['--seed', '1']]:
            with self.assertRaises(ValueError):
                verify_fixed_inputs(self.baseline, bad)


if __name__ == '__main__':
    unittest.main()
