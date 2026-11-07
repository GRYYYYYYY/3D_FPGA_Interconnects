import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from target_timing import criticalities, physical_slots


class TimingFeedback(unittest.TestCase):
    def test_physical_pin_class_distinguishes_subtiles(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'g.xml'
            p.write_text('<rr_graph><block_types><block_type id="1" name="io"><pin_class><pin>io[4].outpad[0]</pin></pin_class><pin_class><pin>io[7].outpad[0]</pin></pin_class></block_type><block_type id="2" name="clb"><pin_class><pin>clb.I[0]</pin></pin_class></block_type></block_types><grid><grid_loc x="86" y="0" layer="1" block_type_id="1"/></grid><rr_nodes/></rr_graph>')
            classes,grid=physical_slots(p)
            self.assertEqual(classes[1],[{4},{7}]);self.assertEqual(classes[2],[{0}]);self.assertEqual(grid[(86,0,1)],1)

    def test_pin_to_cluster_aggregation_and_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            mapping={'atoms':{'a.with.dot':'clb0','b':'clb0','c':'clb1'},'connections':[
                {'net':5,'name':'net','sink':31,'cluster':'clb0'},
                {'net':5,'name':'net','sink':72,'cluster':'clb1'}]}
            (p/'mapping.json').write_text(json.dumps(mapping))
            (p/'sta.log').write_text('Completed routing consistency check successfully\nFinal critical path delay (least slack): 10 ns\n')
            def report(sinks):
                with (p/'net.csv').open('w',newline='') as f:
                    w=csv.DictWriter(f,['netname','sinks']);w.writeheader();w.writerow({'netname':'net','sinks':sinks})
            report('a.with.dot.in[0],-2e-9,1e-9;b.in[1],-8e-9,1e-9;c.in[0],inf,1e-9;')
            meta=criticalities(p/'mapping.json',p/'net.csv',p/'sta.log',p/'priority.txt')
            self.assertEqual((p/'priority.txt').read_text(),'H3DCRITICALITY 1 2\n5 31 800\n5 72 0\n')
            self.assertEqual(meta['connections'],2);self.assertEqual(len(meta['sources']),3)
            report('b.in[1],-8e-9,1e-9;')
            with self.assertRaisesRegex(ValueError,'coverage incomplete'):criticalities(p/'mapping.json',p/'net.csv',p/'sta.log',p/'bad.txt')
            report('b.in[1],nan,1e-9;c.in[0],0,1e-9;')
            with self.assertRaisesRegex(ValueError,'NaN'):criticalities(p/'mapping.json',p/'net.csv',p/'sta.log',p/'bad.txt')
            (p/'sta.log').write_text('Final critical path delay (least slack): 10 ns\n')
            with self.assertRaisesRegex(ValueError,'FULL'):criticalities(p/'mapping.json',p/'net.csv',p/'sta.log',p/'bad.txt')


if __name__=='__main__':unittest.main()
