#!/usr/bin/env python3

import os
import io
import re
import subprocess
import json
import tempfile
from string import Template

ADDED = re.compile('added (?P<hash>[^ ]+) (?P<path>.*)')

p = subprocess.run(['ipfs', 'add', '-r', 'uniswap_predictions_preprocessor'], capture_output=True)
input_cid = best_cid_path_length = None
for line in p.stdout.decode('utf8').split('\n'):
  m = ADDED.match(line)
  if m:
    size = len(m.group('path'))
    if not input_cid or size < best_cid_path_length:
      input_cid = m.group('hash')
      best_cid_path_length = size

print('uploaded to', input_cid)

api_key = os.environ['SPICE_API_KEY']
variables = {
  'api_key': api_key,
  'input_cid': input_cid,
  'flight_address': 'grpc+tls://flight.spiceai.io',
  'query_variables': json.dumps({
    #'block_number': 17216108, # leave out for latest (specific to our test app -- prod will always provide this var)
  }),
}
with open(os.path.join(os.path.dirname(__file__), 'local-job.yaml.tpl'), 'r', encoding='utf8') as f:
    template = Template(f.read())
    spec = template.substitute(variables)
with tempfile.TemporaryDirectory() as d:
  path = os.path.join(d, 'job.yaml')
  with open(path, 'w', encoding='utf8') as f:
    f.write(spec)
  print(subprocess.run(['bacalhau', 'create', path]))
  print('outputs:')
  os.listdir(d)

# testing
if False:
  #print(subprocess.run(['bacalhau', 'create', '--local', path]))
  dry_run = True
  #dry_run = False
  local = False
  docker_image = 'ghcr.io/cod-demo/bacalhau_runner:m1'
  #print(subprocess.run(['bacalhau', 'docker', 'run', '--env', f'SPICE_API_KEY={api_key}'] + (['--dry-run'] if dry_run else []) + (['--local'] if local else []) + ['--network', 'Full', '-i', f'ipfs://{input_cid},dst=/inputs/script', docker_image, '--', 'python3', '/app/run.py']))
  print('outputs:')
  os.listdir(d)

