import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from target_session import TargetSession


class PersistentRouter(unittest.TestCase):
    def fixture(self, directory):
        edges = [(0,1,100),(1,4,1),(1,5,1),(0,2,1),(2,3,1),(3,4,1)]
        graph = 'H3DRRG 1 6 6\n'+''.join(f'{i} 4 1 {i} 0 0 {i} 0 0\n' for i in range(6))
        graph += ''.join(f'{i} {u} {v} 0 {d} 0\n' for i,(u,v,d) in enumerate(edges))
        (directory/'graph.rrg').write_text(graph)
        (directory/'nets.txt').write_text('H3DNETS 1 1\n0 0 2 4 5\n')
        (directory/'delays.txt').write_text('H3DDELAYS 1 6\n'+''.join(f'{i} {d}\n' for i,(_,_,d) in enumerate(edges)))
        (directory/'criticality.txt').write_text('H3DCRITICALITY 1 2\n0 4 990\n0 5 0\n')
        binary = Path(os.environ.get('H3D_TEST_BINARY', ROOT/'build/h3d_route'))
        self.assertTrue(binary.exists(), 'Build h3d_route before running session tests')
        return [binary,directory/'graph.rrg',directory/'nets.txt',directory/'initial.json',
                '--backend','cpu_target','--delay-file',directory/'delays.txt','--bootstrap-criticality','0','--present','1']

    def test_same_process_and_checked_feedback_protocol(self):
        with tempfile.TemporaryDirectory(prefix='h3d session ') as temp:
            directory=Path(temp);session=TargetSession(self.fixture(directory),directory,os.environ.copy())
            try:
                first=session.wait_checkpoint(10)
                second=session.refine(directory/'criticality.txt',directory/'refined.json',10,700,1)
                self.assertEqual(first['checkpoint_code'],0);self.assertEqual(second['checkpoint_code'],0)
                self.assertIsNone(second['returncode']);self.assertEqual(first['session_pid'],second['session_pid'])
                initial=json.loads((directory/'initial.json').read_text());refined=json.loads((directory/'refined.json').read_text())
                self.assertNotEqual(initial['routes'],refined['routes'])
                self.assertTrue(refined['incremental_refinement']);self.assertEqual(refined['refinement_accepted'],1)
            finally:
                exit_record=session.close()
            self.assertEqual(exit_record['returncode'],0)
            self.assertEqual((directory/'session.log').read_text().count('route_phase=graph_read_begin'),1)

    def test_failed_feedback_preserves_prior_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);session=TargetSession(self.fixture(directory),directory,os.environ.copy())
            try:
                self.assertEqual(session.wait_checkpoint(10)['checkpoint_code'],0)
                original=(directory/'initial.json').read_bytes()
                (directory/'criticality.txt').write_text('H3DCRITICALITY 1 1\n0 4 990\n')
                failure=session.refine(directory/'criticality.txt',directory/'bad.json',10)
                self.assertEqual(failure['status'],'failed');self.assertIsNone(failure['checkpoint_code'])
                self.assertNotEqual(failure['returncode'],0)
                self.assertEqual((directory/'initial.json').read_bytes(),original)
                self.assertFalse((directory/'bad.json').exists())
            finally:
                session.close()

    def test_negotiated_feedback_protocol(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);session=TargetSession(self.fixture(directory),directory,os.environ.copy())
            try:
                first=session.wait_checkpoint(10)
                second=session.refine(directory/'criticality.txt',directory/'refined.json',10,700,1,'negotiate')
                self.assertEqual(first['session_pid'],second['session_pid'])
                self.assertEqual(second['checkpoint_code'],0)
                refined=json.loads((directory/'refined.json').read_text())
                self.assertEqual(refined['refinement_mode'],'negotiate');self.assertTrue(refined['refinement_converged'])
                self.assertEqual(refined['iterations'][-1]['overflow'],0)
                self.assertNotEqual(json.loads((directory/'initial.json').read_text())['routes'],refined['routes'])
            finally:
                session.close()


if __name__ == '__main__': unittest.main()
