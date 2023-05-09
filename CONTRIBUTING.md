# How to run local dev loop (simplified version)

Start ipfs

```
make ipfs-fresh-daemon
```

Start bacalhau

```
make bacalhau-devstack
```

Copy and paste the `export ...` lines from above and paste them into a new terminal then run:

```
echo $BACALHAU_IPFS_SWARM_ADDRESSES | cut -d, -f1 | xargs -r ipfs swarm connect
```

Pull down the docker image so that the bacalhau run is fast

```
make pull-image
```

Run the job

```
export SPICE_API_KEY='xxx'
make local-harness
```

View the outputs

```
make ls-outputs id=xxx
make get-result id=xxx
```

## How to run local dev loop

### Start with ipfs

```bash
brew install kubo # this will install ipfs
ipfs init # if you have ~/.ipfs, remove it
ipfs bootstrap rm --all
ipfs daemon
```

### Get bacalhau working

```bash
curl -sL https://get.bacalhau.org/install.sh | bash
bacalhau docker run ubuntu echo Hello World
```

### Start docker in your local

Docker for mac or linux docker

### Start bacalau

```bash
PREDICTABLE_API_PORT=1 bacalhau devstack --job-selection-accept-networked

# Copy all the EXPORT, e.g
# export BACALHAU_IPFS_SWARM_ADDRESSES=/ip4/127.0.0.1/tcp/57300/p2p/Qmd7qJfFKFSBmoiids8Jsoj8cadoWzhykhTZcL1evQrLdv,/ip4/192.168.64.1/tcp/57300/p2p/Qmd7qJfFKFSBmoiids8Jsoj8cadoWzhykhTZcL1evQrLdv
# export BACALHAU_API_HOST=0.0.0.0
# export BACALHAU_API_PORT=20000
# export BACALHAU_PEER_CONNECT=/ip4/192.168.64.1/udp/57289/quic/p2p/Qmd37s635iHLwKC7ugQKSQMXXqPKun3mAgm5PZNFNQv7Mk,/ip4/192.168.64.1/tcp/57294/p2p/QmWLZLAtT31SUfg3TkGk2WCZWs7wmzsU4wxmrf35ZwLXSK,/ip6/::1/tcp/57298/p2p/QmcWSqFdd4CuZd3WmMnpQpRS53NxrYwAYs26Sxyh2aapjQ,/ip4/192.168.64.1/udp/57302/quic/p2p/QmNfKCqPnvTfdjfMPzbqhhsnZgsjpRNNXhGJcGbBKBFiA8
```

### Swarm connect

Take the first part of `BACALHAU_IPFS_SWARM_ADDRESSES` separated by comma, do

```bash
ipfs swarm connect /ip4/127.0.0.1/tcp/57300/p2p/Qmd7qJfFKFSBmoiids8Jsoj8cadoWzhykhTZcL1evQrLdv
```

```bash
export BACALHAU_IPFS_SWARM_ADDRESSES=/ip4/127.0.0.1/tcp/57300/p2p/Qmd7qJfFKFSBmoiids8Jsoj8cadoWzhykhTZcL1evQrLdv,/ip4/192.168.64.1/tcp/57300/p2p/Qmd7qJfFKFSBmoiids8Jsoj8cadoWzhykhTZcL1evQrLdv
export BACALHAU_API_HOST=0.0.0.0
export BACALHAU_API_PORT=20000
export BACALHAU_PEER_CONNECT=/ip4/192.168.64.1/udp/57289/quic/p2p/Qmd37s635iHLwKC7ugQKSQMXXqPKun3mAgm5PZNFNQv7Mk,/ip4/192.168.64.1/tcp/57294/p2p/QmWLZLAtT31SUfg3TkGk2WCZWs7wmzsU4wxmrf35ZwLXSK,/ip6/::1/tcp/57298/p2p/QmcWSqFdd4CuZd3WmMnpQpRS53NxrYwAYs26Sxyh2aapjQ,/ip4/192.168.64.1/udp/57302/quic/p2p/QmNfKCqPnvTfdjfMPzbqhhsnZgsjpRNNXhGJcGbBKBFiA8

# also
export SPICE_API_KEY='xxx'

python3 local_harness.py
```

Check the result

```bash
bacalhau describe bfa7fc58-e34d-4329-ae9c-dd24c877aed0
```

Find CID of output from something like below

```bash
 PublishedResults:
      CID: QmPL8Cxozun9CKzbGEBm9DbJssUozTE43YQB44ZSAa7hky
```

cat the outputs:

```bash
ipfs ls QmPL8Cxozun9CKzbGEBm9DbJssUozTE43YQB44ZSAa7hky
ipfs cat QmPL8Cxozun9CKzbGEBm9DbJssUozTE43YQB44ZSAa7hky/outputs/results.csv
```
