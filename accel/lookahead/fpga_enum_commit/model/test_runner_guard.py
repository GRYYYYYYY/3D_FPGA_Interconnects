"""Cheap self-process sentinels only; never starts any model binary."""
from pathlib import Path
import sys,os,json,tempfile,hashlib,datetime
from unittest.mock import patch
import run

def main():
 out=Path(sys.argv[1]);out.mkdir(exist_ok=False);start=run.now();runtime=run.OUT;before=run.sha(runtime/'bin/model');checks=[]
 with tempfile.TemporaryDirectory(prefix='enum_model_guard_') as tmp:
  run.OUT=Path(tmp)/'run';root=run.OUT/'runs/sentinel';root.mkdir(parents=True);record=root/'running_0_attempt_1.json';live=run.process_identity(os.getpid());assert live and live['pid']==os.getpid();binding={'binary_sha256':'sentinel-only-no-model','inputs':{'sentinel':{'workload':'unused','golden':'unused'}}}
  current={'pid':os.getpid(),'command':live['command'],'start_utc':datetime.datetime.fromtimestamp(live['process_start_unix'],datetime.timezone.utc).isoformat(),'binary_sha256':binding['binary_sha256'],'process_identity':live}
  def expect_refusal(name,record_value,word='Refusing duplicate'):
   record.write_text(json.dumps(record_value))
   with patch.object(run.subprocess,'Popen',side_effect=AssertionError('A model must never be launched by guard tests')) as spawn:
    try:run.execute(binding,'sentinel',0)
    except RuntimeError as exc:assert word in str(exc),(name,str(exc))
    else:raise AssertionError(name+' accepted a live matching sample')
    assert spawn.call_count==0
   assert not (root/'attempt_2').exists() and not list(root.glob('sample_*_attempt_*.log'))
   checks.append(name)
  expect_refusal('live_exact_PID_command_boot_and_start_ticks',current)
  legacy=dict(current);legacy.pop('process_identity');expect_refusal('live_legacy_UTC_start_identity',legacy)
  ambiguous=dict(current,process_identity=dict(live,start_ticks=live['start_ticks']+1));expect_refusal('same_command_ambiguous_start_refuses_safely',ambiguous)
  mismatch=dict(current,binary_sha256='different-frozen-source');expect_refusal('live_same_command_different_source_refuses',mismatch)
  record.write_text(json.dumps(current))
  try:run.guard_live_run(binding['binary_sha256'])
  except RuntimeError as exc:assert 'Refusing duplicate' in str(exc)
  else:raise AssertionError('Global guard accepted a live original sample')
  checks.append('global_guard_before_any_task_submission')
  unrelated=dict(current,command=['unrelated-process-not-the-original-command']);record.write_text(json.dumps(unrelated));run.guard_live_sample(root,0,binding['binary_sha256']);checks.append('reused_PID_different_command_is_not_original')
  dead=dict(current,pid=int(Path('/proc/sys/kernel/pid_max').read_text())+1);record.write_text(json.dumps(dead));run.guard_live_sample(root,0,binding['binary_sha256']);checks.append('absent_process_does_not_block_recovery')
  record.write_text('{partial')
  try:run.guard_live_sample(root,0,binding['binary_sha256'])
  except RuntimeError as exc:assert 'Cannot verify running record' in str(exc)
  else:raise AssertionError('Incomplete provenance accepted')
  checks.append('incomplete_identity_refuses_instead_of_duplicate')
  lock=Path(tmp)/'exclusive.lock'
  with run.exclusive_lock(lock):
   try:
    with run.exclusive_lock(lock):raise AssertionError('Second independent descriptor acquired lock')
   except RuntimeError as exc:assert 'Another original supervisor/sample owns' in str(exc)
  with run.exclusive_lock(lock):pass
  checks.append('nonblocking_supervisor_and_sample_lock_then_release')
  output=Path(tmp)/'completed.bin';output.write_bytes(b'complete-checkpoint');receipt={'returncode':0,'output_exact':True,'output_path':str(output),'output_sha256':run.sha(output)};(root/'receipt_0.json').write_text(json.dumps(receipt));record.write_text(json.dumps(current))
  with patch.object(run.subprocess,'Popen',side_effect=AssertionError('Completed checkpoint must be reused')) as spawn:assert run.execute(binding,'sentinel',0)==receipt;assert spawn.call_count==0
  checks.append('completed_hash_verified_checkpoint_reused_without_launch')
 run.OUT=runtime;after=run.sha(runtime/'bin/model');assert before==after
 result={'all_pass':True,'checks':checks,'command':[sys.executable,*sys.argv],'start_utc':start,'end_utc':run.now(),'returncode':0,'only_self_process_sentinels':True,'model_processes_launched':0,'frozen_D_binary_sha256_before':before,'frozen_D_binary_sha256_after':after,'runner_sha256':run.sha(Path(run.__file__)),'test_source_sha256':run.sha(Path(__file__)),'live_identity_fields_tested':['PID','full argument vector','boot_id','process start ticks','legacy UTC start'],'scope':'runner guard only; no model/runtime architecture or binary changes'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('RUNNER_GUARD_PASS',len(checks),'checks; model launches=0; frozen binary unchanged')
if __name__=='__main__':main()
