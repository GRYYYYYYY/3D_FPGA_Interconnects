"""Logical state ledger; does not infer physical fit from CPU containers."""
from run import *

def main():
 out=R/'model_logical_ledger.json';rows=[]
 def add(name,count,bits,scope='onchip planned',note=''):
  rows.append({'name':name,'count':count,'logical_bits_per_entry':bits,'logical_total_bits':count*bits,'scope':scope,'note':note,'LUT':None,'FF':None,'BRAM36_equivalent':None,'URAM':None,'DSP':None})
 add('pending whole68bit PV words',64*16384,68,note='One read/one write port per subbank; actual local inference from canonical worker, full replication/routing unqualified.')
 add('directory member pool',64*8192,22+28+13+1,note='node22,arg28,next local13+valid1. 64 physically banked fixed pools; no dynamic global capacity sharing.')
 add('directory free indices',64*8192,13,note='one release/allocation service per bank/clock; linked member pointer representation assumes bank-local addressing.')
 add('directory heads+tails',64*4096*2,14,note='local13-bit index+valid; independent head and tail arrays with forwarding required for same bucket.')
 add('directory bucket presence per bank',64*4096,1,note='Full model maintains functional global OR; actual banked presence/reduction routing/selection remains uncalibrated.')
 add('accumulator payload',64*4096*4,64)
 add('accumulator tags/mask',64*4096,36,note='line tag32 in existing RTL plus four-sector mask; native line address actually <=20bits, no unverified compression used.')
 add('accumulator occupied indices',64*4096,12)
 add('accumulator replacement',64*1024,2)
 add('spilled and consumed bitmaps',64*256*2,64,note='Two separate per-subbank bitmaps, clear all 256 words each wave.')
 add('scratch spill IDs',64*2048,20)
 add('target whole seen/pair state',8*4096,65)
 add('front edge payload slots',512,256,note='Reserved/inflight/returned/consuming all share these512; no hidden beat store.')
 add('front edge slot tags/control',512,8+8+32+2,note='generation8,descriptor8,beat sequence32,state2; scheduling timestamps in software are not hardware state.')
 add('front headers',128,22+64+128+8+2+2+2,note='Physical row offsets64x2; node22,pair64,generation8,counts/control. Row payload fields represented by backing-memory accesses gated by responses.')
 add('front E descriptors',256,22+64+32*3+8+3,note='CSR fetched64, physical edge counter32 only after admission checked <2^32 edges; native source counts verified.')
 add('front metadata contexts',128,22+64+40+8+2,note='Returned cell/type payload counted even when software dereferences immutable backing after response.')
 add('fork token',128,22+64+6+16+2+2,note='qid6,epoch16,two consumer bits/state; reservation1/group/clock, later stale releases slot.')
 add('ready-parent',128,22+64+32*2+6+16,note='Eight separate16-entry ready FIFOs.')
 add('pair elastic candidate entries',64*2,22+64,note='Actual FP32 logic/DSP mapping not inferred; this is output storage only.')
 add('candidate router owner FIFO',64*16,22+64)
 add('enum four pipeline data/control upper bound',64*4,12+36+256+1,note='Actual stages hold different subsets; this upper logical envelope is not a physical synthesis estimate.')
 add('enum raw fragment',64,20+4+256+1)
 add('enum fragment FIFO',64*16,20+4+256+1)
 add('scratch query holder',64,20+256+64+1)
 add('scratch merge FIFO',64*16,20+256+1)
 add('canonical commit FIFO',64*16,20+256)
 ctx={'state':4,'node':22,'opcode':3,'sector':2,'generation':8,'operand':64,'line_operand':256,'labels':256,'new_labels':256,'argument':28,'event_one':28,'oldPV':68,'newPV':68,'status':4,'mask':4,'event_arguments':112,'previous_label':64}
 add('K8 canonical transaction record',64*8,sum(ctx.values()),note='Includes at most32 event arguments per bank; do NOT separately add32 complete event FIFO copies. Word locks derive from these records.')
 add('physical request FIFO payload envelope',32*64,32+1+11+256,note='Model shared FIFO64 differs from actual local4xFIFO4; hardware mapping unqualified.')
 add('physical return FIFO',32*4,11+256+2,note='Actual integration also per-client result registers; see next row.')
 add('owner per-client held result register',32*4,11+256+1,note='Actual RTL component, globally abstracted in full model response2-edge contract; not silently claimed cycle-equivalent.')
 add('physical tag restoration',32*32,2+11+1,note='Full top adds front clients and requires expanded/hierarchical route tags; overhead unknown.')
 add('output read/pack reservation FIFO',16,256+32+1,note='Two32B beats/cycle from eight pair-read BRAM banks; finite reserved slots include outstanding two-cycle packing stages.')
 add('pair FP32 adders',64*2,0,scope='logic count only',note='128 real FP32 add operations, targetII1, physical logic/resources unknown until full-top synthesis.')
 profiles={}
 for case in ['bnn_export','lstm_s2']:
  p=json.loads((R/'baseline/profile_a'/case/'physical_profile.json').read_text());s=json.loads((R/'baseline/profile_a'/case/'summary.json').read_text());edges=s['prepared_edges'];assert edges<2**32
  profiles[case]={'nodes':p['nodes'],'prepared_edges':edges,'edge_counter32_admission_pass':True,'canonical_backing_bytes':((p['nodes']+3)//4)*32,'scratch_backing_bytes':((p['nodes']+3)//4)*32,'metadata_backing_bytes_all_samples':p['metadata_sample_stride_lines']*p['jobs']*32,'output_backing_bytes_all_samples':((p['cells']+3)//4+31)//32*32*32*p['jobs']}
 value={'basis':'named logical fields and finite capacities, NOT sizeof(C++ containers)','model_candidate':'model_native_c','rows':rows,'canonical_context_fields':ctx,'external_backing':profiles,'full_kernel_physical_fit_qualified':False,'full_kernel_clock_qualified':False,'physical_resources':{'LUT':None,'FF':None,'BRAM36_equivalent':None,'URAM':None,'DSP':None},'unknown_overhead':['FP32 logic','hierarchical64lane/32owner route and global physical client tags','full directory member/head/tail/free RAM port structure and min-bucket selection','partial RAM packing/replication/placement','init/control/epoch/sample control paths','complete arbitration/register implementation'],'not_mechanical_sum_for_fit':True}
 dump(out,value);print('LOGICAL_LEDGER',len(rows),'rows; no physical fit claim')
if __name__=='__main__':main()
