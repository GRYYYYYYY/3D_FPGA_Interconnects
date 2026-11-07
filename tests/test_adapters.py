import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from audit import audit
from prepare import convert

XML = '''<rr_graph><switches><switch id="0" type="mux"><timing Tdel="1e-12"/></switch></switches>
<rr_nodes>
<node id="10" type="SOURCE" capacity="1"><loc xlow="0" ylow="0" xhigh="0" yhigh="0" layer="0"/></node>
<node id="30" type="CHANZ" capacity="1"><loc xlow="0" ylow="0" xhigh="0" yhigh="0" layer_low="0" layer_high="1"/></node>
<node id="90" type="SINK" capacity="1"><loc xlow="0" ylow="0" xhigh="0" yhigh="0" layer="1"/></node>
</rr_nodes><rr_edges>
<edge src_node="10" sink_node="30" switch_id="0"/>
<edge src_node="10" sink_node="30" switch_id="0"/>
<edge src_node="30" sink_node="90" switch_id="0"/>
</rr_edges></rr_graph>'''
ROUTE = '''Net 7 (test)
Node: 10 SOURCE (0,0,0) Switch: 0
Node: 30 CHANZ (0,0,0) to (0,0,1) Switch: 0
Node: 90 SINK (0,0,1) Switch: -1 Net_pin_index: 1
'''


class Adapters(unittest.TestCase):
    def test_sparse_xml_and_parallel_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'g.xml').write_text(XML)
            (p/'r.route').write_text(ROUTE)
            convert(p/'g.xml',p/'r.route',p/'case')
            manifest = json.loads((p/'case/manifest.json').read_text())
            self.assertEqual(manifest['edges'],3)
            self.assertEqual(manifest['cross_layer_nets'],1)
            subprocess.run([os.environ.get('H3D_TEST_BINARY',str(ROOT/'build/h3d_route')),p/'case/graph.rrg',p/'case/nets.txt',p/'result.json'],check=True,capture_output=True)
            self.assertTrue(audit(p/'case/graph.rrg',p/'case/nets.txt',p/'result.json')['legal_in_projection'])
            value = json.loads((p/'result.json').read_text())
            value['routes'][0]['edges'] = [0]  # Missing terminal arc must be caught.
            (p/'bad.json').write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                audit(p/'case/graph.rrg',p/'case/nets.txt',p/'bad.json')

    def test_reject_nonconfigurable_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'r.route').write_text(ROUTE)
            for kind in ('short','buffer','pass_gate'):
                (p/'g.xml').write_text(XML.replace('type="mux"',f'type="{kind}"'))
                with self.subTest(kind=kind), self.assertRaisesRegex(ValueError,'closure'):
                    convert(p/'g.xml',p/'r.route',p/kind)

    def test_audit_fault_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            graph, nets = ROOT/'examples/two_tier.rrg', ROOT/'examples/two_tier.nets'
            subprocess.run([os.environ.get('H3D_TEST_BINARY',str(ROOT/'build/h3d_route')),graph,nets,p/'result.json'],check=True,capture_output=True)
            original = json.loads((p/'result.json').read_text())
            for fault in ('duplicate','invented_edge','missing_net','false_success','overcapacity'):
                value = json.loads(json.dumps(original))
                if fault=='duplicate': value['routes'][0]['nodes'].append(2)
                if fault=='invented_edge': value['routes'][0]['edges'][0]=999
                if fault=='missing_net': value['routes'].pop()
                if fault=='false_success': value['success']=False
                if fault=='overcapacity':
                    value['routes'][1]['nodes']=[1,2,6]
                    value['routes'][1]['edges']=[1,4]
                (p/'bad.json').write_text(json.dumps(value))
                with self.subTest(fault=fault), self.assertRaises(ValueError):
                    audit(graph,nets,p/'bad.json')


if __name__=='__main__': unittest.main()
