# Tendermint RPC Client

Python based client to interact with a Tendermint node. This API contains a subset of the full [Tendermint API](https://docs.tendermint.com/master/rpc/)


## Example
```python
from tendermint import RpcClient

# defaults to localhost node. See other params
client = RpcClient()

# Calls return (True | False,  Data: dict)
# 'True' == success.  'Data' will contain result
# 'False' == error. 'Data' will contain error information
ok, data = client.status()
ok, data = client.net_info()

ok, data = client.broadcast_tx_commit("0x1")
```


