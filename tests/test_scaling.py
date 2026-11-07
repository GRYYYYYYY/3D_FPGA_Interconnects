import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare import xml_database
from scaling_common import metrics, quality_comparison


class ScalingProtocol(unittest.TestCase):
    def test_failure_cannot_become_speedup(self):
        ref={'success':True,'critical_path_ns':10,'wirelength':100,'routing_seconds':10,
             'process_seconds':15,'workflow_seconds':15}
        self.assertFalse(quality_comparison(ref,{'success':False,'process_seconds':1})['eligible'])
        candidate=dict(ref,critical_path_ns=11,wirelength=104,workflow_seconds=20,process_seconds=2)
        result=quality_comparison(ref,candidate)
        self.assertGreater(result['process_speedup'],1)
        self.assertLess(result['workflow_speedup'],1)
        self.assertFalse(result['quality_bands']['5'])
        self.assertTrue(result['quality_bands']['20'])

    def test_native_failure_metrics_remain_separate(self):
        data=metrics('Routing took 1.2 seconds.\nTime spent on path search: 0.4 seconds.\n'
                     'Final critical path delay (least slack): 5.2 ns\nTotal wirelength: 99')
        self.assertFalse(data['full_check'])
        self.assertFalse(data['routing_success'])
        self.assertEqual(data['search_seconds'],0.4)

    def test_persistent_xml_retains_export_coordinates_and_edge_identity(self):
        xml='''<rr_graph><switches><switch id="3" type="mux"><timing Tdel="1e-12"/></switch></switches>
        <rr_nodes><node id="9" type="CHANZ" capacity="1"><loc xlow="1" ylow="2" xhigh="1" yhigh="2"
        layer_low="0" layer_high="1" ptc="7"/><timing R="0" C="0"/></node></rr_nodes>
        <rr_edges><edge src_node="9" sink_node="9" switch_id="3"/>
        <edge src_node="9" sink_node="9" switch_id="3"/></rr_edges></rr_graph>'''
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/'graph.xml').write_text(xml);xml_database(p/'graph.xml',p/'graph.sqlite')
            with sqlite3.connect(p/'graph.sqlite') as db:
                self.assertEqual(db.execute('SELECT ptc,layer_low,layer_high FROM nodes').fetchone(),('7',0,1))
                self.assertEqual(db.execute('SELECT id FROM edges ORDER BY id').fetchall(),[(0,),(1,)])
                self.assertIn('sha256',json.loads(db.execute('SELECT value FROM metadata').fetchone()[0])['source'])


if __name__=='__main__':unittest.main()
