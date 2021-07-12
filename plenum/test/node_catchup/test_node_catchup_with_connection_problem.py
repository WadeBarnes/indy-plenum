import pytest
from plenum.common.config_helper import PNodeConfigHelper
from plenum.common.messages.node_messages import LedgerStatus, ConsistencyProof
from plenum.common.util import getCallableName
from plenum.server.router import Route
from plenum.test.helper import sdk_send_random_and_check
from plenum.test.node_catchup.helper import waitNodeDataEquality
from plenum.test.pool_transactions.helper import \
    disconnect_node_and_ensure_disconnected
from plenum.test.test_node import checkNodesConnected, TestNode
from plenum.test.view_change.helper import start_stopped_node
from stp_core.types import HA

import logging
logger = logging.getLogger()

call_count = 0


@pytest.fixture(scope='function', params=range(1, 5))
def lost_count(request):
    return request.param


def test_catchup_with_lost_ledger_status(txnPoolNodeSet,
                                         looper,
                                         sdk_pool_handle,
                                         sdk_wallet_steward,
                                         tconf,
                                         tdir,
                                         allPluginsPath,
                                         monkeypatch,
                                         lost_count):
    '''Skip processing of lost_count Message Responses with LEDGER STATUS
    in catchup; test makes sure that the node eventually finishes catchup'''

    node_to_disconnect = txnPoolNodeSet[-1]
    
    logger.warning(f"lost_count: {lost_count}")
    logger.warning(f"txnPoolNodeSet: {txnPoolNodeSet}")
    logger.warning(f"looper: {looper}")
    logger.warning(f"sdk_pool_handle: {sdk_pool_handle}")
    logger.warning(f"sdk_wallet_steward: {sdk_wallet_steward}")
    logger.warning(f"tconf: {tconf}")
    logger.warning(f"tdir: {tdir}")
    logger.warning(f"allPluginsPath: {allPluginsPath}")
    logger.warning(f"monkeypatch: {monkeypatch}")
    logger.warning(f"node_to_disconnect: {node_to_disconnect}")

    logger.warning(f"sdk_send_random_and_check")
    sdk_send_random_and_check(looper, txnPoolNodeSet,
                              sdk_pool_handle, sdk_wallet_steward, 5)

    # restart node
    logger.warning(f"Restart node; {node_to_disconnect} ...")

    logger.warning(f"Disconnect node; {node_to_disconnect} ...")
    disconnect_node_and_ensure_disconnected(looper,
                                            txnPoolNodeSet,
                                            node_to_disconnect)

    logger.warning(f"looper.removeProdable; {node_to_disconnect.name} ...")
    looper.removeProdable(name=node_to_disconnect.name)

    logger.warning(f"sdk_send_random_and_check ...")
    sdk_send_random_and_check(looper, txnPoolNodeSet,
                              sdk_pool_handle, sdk_wallet_steward,
                              2)

    logger.warning(f"Get nodeHa and nodeCHa ...")
    nodeHa, nodeCHa = HA(*node_to_disconnect.nodestack.ha), HA(
        *node_to_disconnect.clientstack.ha)

    logger.warning(f"Get config helper for {node_to_disconnect.name} ...")
    config_helper = PNodeConfigHelper(node_to_disconnect.name, tconf,
                                      chroot=tdir)

    logger.warning(f"Test disconnected node ...")
    node_to_disconnect = TestNode(node_to_disconnect.name,
                                  config_helper=config_helper,
                                  config=tconf,
                                  ha=nodeHa, cliha=nodeCHa,
                                  pluginPaths=allPluginsPath)
    logger.warning(f"node_to_disconnect: {node_to_disconnect}")

    def unpatch_after_call(status, frm):
        global call_count
        call_count += 1
        logger.warning(f"unpatch_after_call::call_count: {call_count}")
        if call_count >= lost_count:
            # unpatch processLedgerStatus after lost_count calls
            logger.warning(f"unpatching processLedgerStatus after lost_count calls ...")
            node_to_disconnect.nodeMsgRouter.add((LedgerStatus, node_to_disconnect.ledgerManager.processLedgerStatus))
            call_count = 0

    # patch processLedgerStatus
    logger.warning(f"patch processLedgerStatus ...")
    node_to_disconnect.nodeMsgRouter.add((LedgerStatus, unpatch_after_call))

    # add node_to_disconnect to pool
    logger.warning(f"add node_to_disconnect to pool ...")
    looper.add(node_to_disconnect)
    txnPoolNodeSet[-1] = node_to_disconnect
    looper.run(checkNodesConnected(txnPoolNodeSet))

    logger.warning(f"waitNodeDataEquality ...")
    waitNodeDataEquality(looper, node_to_disconnect, *txnPoolNodeSet,
                         exclude_from_check=['check_last_ordered_3pc_backup'],
                         customTimeout=20)


def test_catchup_with_lost_first_consistency_proofs(txnPoolNodeSet,
                                                    looper,
                                                    sdk_pool_handle,
                                                    sdk_wallet_steward,
                                                    tconf,
                                                    tdir,
                                                    allPluginsPath,
                                                    monkeypatch,
                                                    lost_count):
    '''Skip processing of first lost_count CONSISTENCY_PROOFs in catchup. In
    this case catchup node has no quorum with f+1 CONSISTENCY_PROOFs for the
    longer transactions list. It need to request CONSISTENCY_PROOFs again and
    finishes catchup.
    Test makes sure that the node eventually finishes catchup'''
    node_to_disconnect = txnPoolNodeSet[-1]

    sdk_send_random_and_check(looper, txnPoolNodeSet,
                              sdk_pool_handle, sdk_wallet_steward, 5)

    # restart node
    disconnect_node_and_ensure_disconnected(looper,
                                            txnPoolNodeSet,
                                            node_to_disconnect)
    looper.removeProdable(name=node_to_disconnect.name)
    sdk_send_random_and_check(looper, txnPoolNodeSet,
                              sdk_pool_handle, sdk_wallet_steward,
                              2)

    nodeHa, nodeCHa = HA(*node_to_disconnect.nodestack.ha), HA(
        *node_to_disconnect.clientstack.ha)
    config_helper = PNodeConfigHelper(node_to_disconnect.name, tconf,
                                      chroot=tdir)
    node_to_disconnect = TestNode(node_to_disconnect.name,
                                  config_helper=config_helper,
                                  config=tconf,
                                  ha=nodeHa, cliha=nodeCHa,
                                  pluginPaths=allPluginsPath)

    def unpatch_after_call(proof, frm):
        global call_count
        call_count += 1
        if call_count >= lost_count:
            # unpatch processConsistencyProof after lost_count calls
            node_to_disconnect.nodeMsgRouter.add((ConsistencyProof,
                                                  node_to_disconnect.ledgerManager.processConsistencyProof))
            call_count = 0

    # patch processConsistencyProof
    node_to_disconnect.nodeMsgRouter.add((ConsistencyProof, unpatch_after_call))
    # add node_to_disconnect to pool
    looper.add(node_to_disconnect)
    txnPoolNodeSet[-1] = node_to_disconnect
    looper.run(checkNodesConnected(txnPoolNodeSet))
    waitNodeDataEquality(looper, node_to_disconnect, *txnPoolNodeSet,
                         exclude_from_check=['check_last_ordered_3pc_backup'])


def test_cancel_request_cp_and_ls_after_catchup(txnPoolNodeSet,
                                                looper,
                                                sdk_pool_handle,
                                                sdk_wallet_steward,
                                                tconf,
                                                tdir,
                                                allPluginsPath):
    '''Test cancel of schedule with requesting ledger statuses and consistency
    proofs after catchup.'''
    node_to_disconnect = txnPoolNodeSet[-1]
    sdk_send_random_and_check(looper, txnPoolNodeSet,
                              sdk_pool_handle, sdk_wallet_steward, 5)

    # restart node
    disconnect_node_and_ensure_disconnected(looper,
                                            txnPoolNodeSet,
                                            node_to_disconnect)
    looper.removeProdable(name=node_to_disconnect.name)
    sdk_send_random_and_check(looper, txnPoolNodeSet,
                              sdk_pool_handle, sdk_wallet_steward,
                              2)
    # add node_to_disconnect to pool
    node_to_disconnect = start_stopped_node(node_to_disconnect, looper, tconf,
                                            tdir, allPluginsPath)
    txnPoolNodeSet[-1] = node_to_disconnect
    looper.run(checkNodesConnected(txnPoolNodeSet))
    waitNodeDataEquality(looper, node_to_disconnect, *txnPoolNodeSet,
                         exclude_from_check=['check_last_ordered_3pc_backup'])

    # check cancel of schedule with requesting ledger statuses and consistency proofs
    for event in node_to_disconnect.timer._events:
        name = event.callback.__name__
        assert name != '_reask_for_ledger_status'
        assert name != '_reask_for_last_consistency_proof'
