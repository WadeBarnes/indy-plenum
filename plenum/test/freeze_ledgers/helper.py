import json
from typing import List

from indy_vdr import ledger
from plenum.test.helper import vdr_get_and_check_replies, \
    vdr_send_signed_requests, vdr_sign_and_submit_req_obj, vdr_multi_sign_request_objects, vdr_json_to_request_object


def vdr_send_freeze_ledgers(looper, vdr_pool_handle, vdr_wallets, ledgers_ids: List[int]):
    req = ledger.build_ledgers_freeze_request(vdr_wallets[0][1], ledgers_ids)
    signed_reqs = vdr_multi_sign_request_objects(looper, vdr_wallets,
                                                 [req])
    reps = vdr_send_signed_requests(vdr_pool_handle, signed_reqs, looper)
    return vdr_get_and_check_replies(looper, reps)[0]


# vdr_wallet needs to be DID with new function since wallet no longer tuple
def vdr_get_frozen_ledgers(looper, vdr_pool_handle, vdr_wallet):
    req = ledger.build_get_frozen_ledgers_request(vdr_wallet[1])
    rep = vdr_sign_and_submit_req_obj(looper, vdr_pool_handle, vdr_wallet, req)
    return vdr_get_and_check_replies(looper, [rep])[0]
