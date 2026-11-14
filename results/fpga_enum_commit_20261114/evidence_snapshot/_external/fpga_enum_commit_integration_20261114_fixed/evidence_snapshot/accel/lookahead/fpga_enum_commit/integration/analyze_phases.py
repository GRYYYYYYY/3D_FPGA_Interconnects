from pathlib import Path
import csv,json,sys
root=Path(sys.argv[1]);out=[]
for v in [0,1]:
 rows=list(csv.DictReader((root/f'metrics_{v}.csv').open()));n=0;last=int(rows[0]['start']);start=last;end=int(rows[0]['end'])
 for t in csv.DictReader((root/f'trace_{v}.csv').open()):
  cycle=int(t['cycle'])
  while cycle>end:
   d=rows[n];out.append({'variant':v,'case':d['case'],'wave':int(d['wave']),'start':start,'last_candidate_accept':last,'end':end,'start_to_last_candidate_cycles':last-start,'after_last_candidate_until_all_retired_cycles':end-last});n+=1
   d=rows[n];start=int(d['start']);end=int(d['end']);last=start
  if int(t['candidate_accept']):last=cycle
 while n<len(rows):
  d=rows[n];out.append({'variant':v,'case':d['case'],'wave':int(d['wave']),'start':int(d['start']),'last_candidate_accept':last if n==len(rows)-1 else int(d['start']),'end':int(d['end']),'start_to_last_candidate_cycles':last-int(d['start']) if n==len(rows)-1 else 0,'after_last_candidate_until_all_retired_cycles':int(d['end'])-last if n==len(rows)-1 else int(d['cycles'])});n+=1
(root/'phase_analysis.json').write_text(json.dumps({'scope':'wall boundaries, no sum of overlappingbusy times; final tail includes candidatepipeline drain and allACK/PV/directory retirement','rows':out},indent=2))
for x in out:
 if x['case'].startswith(('bnn','lstm','hot_set')):print(x['variant'],x['case'],x['wave'],x['start_to_last_candidate_cycles'],x['after_last_candidate_until_all_retired_cycles'])
