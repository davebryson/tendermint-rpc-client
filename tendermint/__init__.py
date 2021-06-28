"""
Tendermint RPC client: json-rpc requests over HTTP
"""
import json
import requests
import itertools
import base64

from typing import Union, Tuple

BytesOrStr = Union[str, bytes, bytearray]
Result = Tuple[bool, dict]
Json = str


PORT = 26657
AGENT = "tmrpc/0.2"
HEADERS = {"user-agent": AGENT, "Content-Type": "application/json"}


class RpcClient:
    def __init__(self, scheme="http", host="127.0.0.1", port=PORT):
        # Tendermint node endpoint
        self.uri = "{}://{}:{}".format(scheme, host, port)

        # Keep a session
        self.session = requests.Session()

        # Request counter for json-rpc
        self.request_counter = itertools.count()

    def _dispatch(self, method, params) -> Result:
        value = str(next(self.request_counter))
        encoded = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or [],
                "id": value,
            }
        )

        r = self.session.post(self.uri, data=encoded, headers=HEADERS, timeout=3)
        response = r.json()
        if response.get("error", None):
            return (False, response["error"])
        return (True, response["result"])

    @property
    def can_connect(self) -> bool:
        """
        Simple connectivity test
        """
        try:
            response = self.status
            assert response["node_info"]
            return True
        except IOError:
            return False

    ## Info API ##

    def status(self) -> Result:
        """
        Node status
        """
        return self._dispatch("status", [])

    def net_info(self) -> Result:
        """
        Network Information
        """
        return self._dispatch("net_info", [])

    def genesis(self) -> Result:
        """
        Get genesis information
        """
        return self._dispatch("genesis", [])

    def unconfirmed_txs(self) -> Result:
        """
        Get list of unconfirmed transaction (Defaults to 30)
        """
        return self._dispatch("unconfirmed_txs", [])

    def num_unconfirmed_txs(self) -> Result:
        """
        Get information about unconfirmed transactions
        """
        return self._dispatch("num_unconfirmed_txs", [])

    def validators(self, height=1) -> Result:
        """
        Get current validators. Validators are sorted first by voting power (descending), then by address (ascending).
        """
        return self._dispatch("validators", [str(height), str(1), str(30)])

    def get_block(self, height: int = 1) -> Result:
        """
        Get a block at the specified height.  If no height is given, return the latest
        """
        if height <= 0:
            return self._dispatch("block", [])
        else:
            return self._dispatch("block", [str(height)])

    ## ABCI API

    def app_info(self) -> Result:
        """
        Get information about the ABCI application
        """
        ok, data = self._dispatch("abci_info", [])
        if ok:
            return (ok, data.get("response", None))
        return (False, data)

    def app_query(
        self, path: str, data: BytesOrStr, height: int = 1, proof: bool = False
    ) -> Result:
        """
        Query the application.  This depends on how the query is implemented
        in the ABCI application.
        Except 'data' as str or bytes and convert to hex with 0x
        """
        if isinstance(data, str):
            bits = data.encode("utf-8")
            r, data = self._dispatch(
                "abci_query", [path, "{}".format(bits.hex()), str(height), proof]
            )
            return (True, data.get("response", None))
        elif isinstance(data, (bytes, bytearray)):
            r = self._dispatch(
                "abci_query", [path, "{}".format(data.hex()), str(height), proof]
            )
            return (True, data.get("response", None))
        else:
            return (False, {"log": "query data should be 'str' or 'bytes"})

    ## Transaction API
    ## According to here:
    ## https://docs.tendermint.com/master/tendermint-core/using-tendermint.html#formatting
    ## Json POST:  Hex must be base64 encoded. It's not clear what to do with str...

    def _send_transaction(self, name, tx: BytesOrStr) -> Result:
        if isinstance(tx, str):
            return self._dispatch(name, [tx])
        elif isinstance(tx, (bytes, bytearray)):
            # hex it, then base64 it
            tx1 = base64.b64encode(tx.hex()).decode("utf-8")
            return self._dispatch(name, [tx1])
        else:
            raise ValueError("tx expects either str or bytes")

    def send_tx_commit(self, tx) -> Result:
        """ """
        return self._send_transaction("broadcast_tx_commit", tx)

    def send_tx_sync(self, tx) -> Result:
        """ """
        return self._send_transaction("broadcast_tx_sync", tx)

    def send_tx_async(self, tx) -> Result:
        """ """
        return self._send_transaction("broadcast_tx_async", tx)
