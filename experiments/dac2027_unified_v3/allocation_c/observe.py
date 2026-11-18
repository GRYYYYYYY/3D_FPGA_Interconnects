"""Poll the single submitted recovery and archive its terminal evidence."""
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

here = Path(__file__).resolve().parent
audit = here/'audit'
run = here/'run'
observer = here/'observer'
observer.mkdir(exist_ok=True)
sys.path.insert(0,str(here.parents[4]/'codex/home/skills/inspire-gpu-submit/scripts'))
import inspire_gpu


def write(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n')
    tmp.replace(path)


def main():
    with (observer/'observer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        job = json.loads((audit/'submission.json').read_text())['submission']['Result']['job_id']
        while True:
            try:
                status = inspire_gpu.qz_data('train','GetJob',{'job_id':job})['Result']
            except inspire_gpu.QzError as error:
                print(f'Retrying read-only job status: {error}',flush=True)
                time.sleep(60)
                continue
            fields = ('job_id','status','timeline','finished_at','running_time_ms')
            state = {k:status.get(k) for k in fields}
            state['formal_records'] = len(list((run/'formal/lstm').glob('*/*/record.json')))
            state['readbacks'] = len(list((run/'formal/lstm').glob('*/*/readback/record.json')))
            write(observer/'status.json',state)
            if status.get('finished_at'):
                break
            time.sleep(60)
        write(audit/'terminal.json',state)
        for name in ('environment.json','checkpoint.json'):
            source = run/name
            if source.is_file():
                shutil.copyfile(source,audit/name)
        if (run/'checkpoint.json').is_file() and not (audit/'verification.json').is_file():
            instances = inspire_gpu.qz_data('train','ListJobInstances',
                {'job_id':job,'page_number':1,'page_size':10})['Result']['items']
            events = inspire_gpu.qz_data('train','ListJobEvents',
                {'page_number':1,'page_size':50,'filter':{'object_type':'job','object_ids':[job]}})['Result']['events']
            write(audit/'allocation_stop.json',dict(state,instances=instances,
                stop_events=[entry for entry in events if entry['reason']=='StopJob']))
            if state['status']=='job_stopped' or (run/'finished.json').is_file():
                for entry in ('closeout.py','validate.py'):
                    subprocess.run([sys.executable,entry],cwd=here.parent,check=True)
        print(state,flush=True)


if __name__=='__main__':
    main()
