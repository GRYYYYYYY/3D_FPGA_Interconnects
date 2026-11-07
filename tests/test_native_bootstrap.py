import errno
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from bootstrap_native_diagnostics import mirror_small_files


class MirrorRecovery(unittest.TestCase):
    def test_quota_error_preserves_prior_live_file_and_does_not_raise(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);run=root/'run';out=root/'out';run.mkdir();(out/'live').mkdir(parents=True)
            (run/'summary.json').write_text('new');(out/'live/summary.json').write_text('old')
            with patch('bootstrap_native_diagnostics.shutil.copyfile',side_effect=OSError(errno.EDQUOT,'Disk quota exceeded')):
                errors=mirror_small_files(run,out)
            self.assertEqual(len(errors),1);self.assertEqual((out/'live/summary.json').read_text(),'old')
            self.assertFalse((out/'live/summary.json.mirror_tmp').exists())
    def test_successful_mirror_includes_overuse_report(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);run=root/'run';run.mkdir();(run/'overuse.rpt').write_text('node 3')
            self.assertEqual(mirror_small_files(run,root/'out'),[])
            self.assertEqual((root/'out/live/overuse.rpt').read_text(),'node 3')


if __name__=='__main__':unittest.main()
