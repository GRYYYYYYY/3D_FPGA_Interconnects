from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native_cpu_budget import choose_cores


class PhysicalBudget(unittest.TestCase):
    def test_smt_siblings_do_not_count_as_separate_cores(self):
        t=[{'cpu':c,'socket':0,'core':c%4,'node':0} for c in range(8)]
        self.assertEqual(choose_cores(t,4),[0,1,2,3])
        with self.assertRaises(ValueError):choose_cores(t,5)
    def test_gpu_numa_preference(self):
        t=[{'cpu':c,'socket':c//4,'core':c%4,'node':c//4} for c in range(8)]
        self.assertEqual(choose_cores(t,4,1),[4,5,6,7])
    def test_duplicate_core_ids_on_different_sockets_are_distinct(self):
        t=[{'cpu':c,'socket':c,'core':0,'node':c} for c in range(4)]
        self.assertEqual(choose_cores(t,4),[0,1,2,3])


if __name__=='__main__':unittest.main()
