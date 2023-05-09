export BACALHAU_API_HOST=0.0.0.0
export BACALHAU_API_PORT=20000

ipfs-fresh-daemon:
	killall ipfs || true
	rm -rf ~/.ipfs
	ipfs init
	ipfs bootstrap rm --all
	ipfs daemon

bacalhau-devstack:
	killall bacalhau || true
	PREDICTABLE_API_PORT=1 bacalhau devstack --job-selection-accept-networked

local-harness:
	 python3 local_harness.py

ls-outputs:
	$(eval cid=$(shell bacalhau describe $(id) | grep -A2 PublishedResults | grep CID | cut -d ":" -f 2 | xargs))
	@ipfs ls $(cid)

get-result:
	$(eval cid=$(shell bacalhau describe $(id) | grep -A2 PublishedResults | grep CID | cut -d ":" -f 2 | xargs))
	@ipfs cat $(cid)/outputs/results.csv

pull-image:
	docker pull ghcr.io/cod-demo/bacalhau_runner:m1

.PHONY: ipfs-fresh-daemon bacalhau-devstack local-harness ls-outputs get-result pull-image
