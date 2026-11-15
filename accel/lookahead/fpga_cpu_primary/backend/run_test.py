"""Run one source-bound production-bank test in a new directory, never overwrite."""
from pathlib import Path
import argparse,json,subprocess,sys
R=Path(__file__).resolve().parents[4];S=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('out');a=p.parse_args()
files=json.loads((S/'sources.json').read_text())+[str((S/'tb_backend_bank.sv').relative_to(R))]
subprocess.run([sys.executable,str(R/'accel/lookahead/fpga_local_fabric/delivery/simulate.py'),a.out,'tb_backend_bank',*[str(R/x)for x in files]],cwd=R,check=True)
