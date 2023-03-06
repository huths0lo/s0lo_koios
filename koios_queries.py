import requests
from time import sleep
import pandas as pd
from common_functions import name_2_hex
from bech32_tools import wallet_to_stake, get_asset_fingerprint

handle_policy = 'f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a'





def get_stake_utxos(stake_key, api_base_url):
    all_utxos = []
    wallet_addresses = get_account_addresses(stake_key, api_base_url)
    if wallet_addresses == None:
        return []
    sleep(.1)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = f'\u007b"_addresses":['
    for wallet in wallet_addresses:
        payload += f'"{wallet}",'
    payload = payload[:len(payload) - 1]
    payload += ']\u007d'
    response = requests.post(url=f'{api_base_url}/address_info', headers=headers, data=payload, timeout=10)
    status = response.status_code
    if status != 200:
        return []
    else:
        response = response.json()
    all_address_utxos = response
    for address in all_address_utxos:
        if int(address['balance']) != 0:
            all_utxos.append(address)
    if len(all_utxos) == 0:
        return []
    utxos = pd.DataFrame(index=None)
    for item in all_utxos:
        utxo_row = pd.DataFrame(item['utxo_set']).astype({'value': 'str'}).astype({'value': 'int'}).rename(columns={'tx_hash': 'TxHash', 'tx_index': 'TxIx', 'value': 'Lovelace'})
        utxo_row = utxo_row.sort_values(by=['block_time'], ascending=True)
        utxos = pd.concat([utxos, utxo_row])
    utxos.reset_index(drop=True, inplace=True)
    return utxos





def get_account_addresses(stake_addr, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_stake_addresses":["{stake_addr}"]\u007d'
    response = requests.post(f'{api_base_url}/account_addresses', headers=headers, data=data, timeout=10)
    status = response.status_code
    response = response.json()
    if status != 200 or len(response) == 0:
        return []
    return response[0]['addresses']











def api_base_url_from_wallet(wallet):
    if wallet[:6] == 'stake_' or wallet[:5] == 'addr_':
        api_base_url = 'https://preprod.koios.rest/api/v0'
    else:
        api_base_url = 'https://api.koios.rest/api/v0'
    return api_base_url


def get_sender_address(tx_hash, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_tx_hashes":["{tx_hash}"]\u007d'
    print('Getting Address')
    response = requests.post(f'{api_base_url}/tx_info', headers=headers, data=data, timeout=10)
    if response.status_code != 200:
        return None
    response = response.json()
    sender_addr = response[0]['inputs'][0]['payment_addr']['bech32']
    return sender_addr


def get_first_used_address(stake_key, api_base_url):
    first_addr = None
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"]\u007d'
    print('Getting Address')
    response = requests.post(f'{api_base_url}/account_addresses', headers=headers, data=data, timeout=10)
    if response.status_code != 200:
        return None
    response = response.json()
    if len(response) != 0:
        first_addr = response[0]['addresses'][0]
    return first_addr



def get_pool_info(pool_id, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_pool_bech32_ids":["{pool_id}"]\u007d'
    response = requests.post(f'{api_base_url}/pool_info', headers=headers, data=data, timeout=10)
    if response.status_code != 200:
        return None
    pool_info = response.json()
    return pool_info


def get_delegate_info(stake_key, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"]\u007d'
    response = requests.post(f'{api_base_url}/account_info', headers=headers, data=data, timeout=10)
    if response.status_code != 200:
        return None
    delegate_info = response.json()
    delegate_info[0]['pool_info'] = get_pool_info(delegate_info[0]['delegated_pool'], api_base_url)
    return delegate_info



def get_delegate_by_epoch(stake_key, api_base_url, epoch):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"],"_epoch_no": {epoch}\u007d'
    response = requests.post(f'{api_base_url}/account_history', headers=headers, data=data, timeout=10)
    if response.status_code == 200:
        delegate_info = response.json()
        if len(delegate_info) == 0:
            return None, None
        pool_id = delegate_info[0]['history'][0]['pool_id']
        delegated = int(delegate_info[0]['history'][0]['active_stake'])
    return pool_id, delegated


def get_pool_delegates(bech_pool_id, api_base_url, epoch=None):
    headers = {'Accept': 'application/json'}
    if epoch == None:
        epoch, tip = get_epoch_tip(api_base_url)
    print('Checking Delegation')
    response = requests.get(f'{api_base_url}/pool_delegators_history?_pool_bech32={bech_pool_id}&_epoch_no={epoch}', headers=headers, timeout=30)
    if response.status_code != 200:
        return None
    pool_delegates = response.json()
    return pool_delegates




def get_epoch_tip(api_base_url):
    sleep(1)
    headers = {'Accept': 'application/json'}
    print('Quering Epoch')
    response = requests.get(f'{api_base_url}/tip', headers=headers, timeout=10)
    if response.status_code != 200:
        return None, None
    epoch_tip = response.json()
    epoch = int(epoch_tip[0]['epoch_no'])
    tip = int(epoch_tip[0]['abs_slot'])
    return epoch, tip





def get_wallet_assets(stake_key, api_base_url):
    sleep(.1)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"]\u007d'
    response = requests.post(f'{api_base_url}/account_assets', data=data, headers=headers, timeout=10)
    if response.status_code != 200:
        return None
    wallet_contents = response.json()
    return wallet_contents






def get_epoch_params(api_base_url, epoch=None):
    if epoch == None:
        epoch = get_epoch_tip(api_base_url)[0]
    headers = {
        'Accept': 'application/json',
    }
    response = requests.get(f'{api_base_url}/epoch_params?_epoch_no={epoch}', headers=headers, timeout=10)
    if response.status_code != 200:
        return None
    epoch_params = response.json()
    return epoch_params


def assets_from_policy(policy_id, api_base_url):
    sleep(1)
    headers = {'Accept': 'application/json'}
    print('Quering Policy')
    response = requests.get(f'{api_base_url}/asset_policy_info?_asset_policy={policy_id}', headers=headers, timeout=30)
    if response.status_code != 200:
        return None
    asset_json = response.json()
    if len(asset_json) == 0:
        return None
    all_assets = pd.DataFrame(data=None, index=None, columns=['asset_name', 'quantity'])
    i = 0
    while i < len(asset_json):
        asset_name = asset_json[i]['asset_name_ascii']
        quantity = int(asset_json[i]['total_supply'])
        if 'minting_tx_metadata' in asset_json[i]:
            if quantity != 0 and asset_json[i]['minting_tx_metadata']['key'] == '721':
                temp_row = pd.DataFrame([[asset_name, quantity]], columns=['asset_name', 'quantity'])
                all_assets = pd.concat([all_assets, temp_row])
        i += 1
    all_assets.reset_index(drop=True, inplace=True)
    return all_assets

def check_fungible_tag(tx_hash, api_base_url):
    print('Checking if this is a fungible reload')
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = f'\u007b"_tx_hashes":["{tx_hash}"]\u007d'
    try:
        response = requests.post(url=f'{api_base_url}/tx_metadata', headers=headers, data=payload, timeout=10)
    except:
        return False
    if response.status_code == 200:
        check_meta = response.json()
    if check_meta[0]['metadata'] != None:
        if '674' in check_meta[0]['metadata']:
            if 'msg' in check_meta[0]['metadata']['674']:
                if 'fungible' in check_meta[0]['metadata']['674']['msg'].lower():
                    return True
    return False



def get_cardano_price():
    cardano_price = None
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd", timeout=10)
    if response.status_code == 200:
        cardano_price = response.json()['cardano']['usd']
    return cardano_price


def get_utxos(wallet_address, api_base_url, filter_handles=False, filter_assets=False):
    sleep(1)
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = f'\u007b"_addresses":["{wallet_address}"]\u007d'
    try:
        response = requests.post(url=f'{api_base_url}/address_info', headers=headers, data=payload, timeout=10)
    except:
        return 'timed_out'
    if response.status_code != 200:
        return 'timed_out'
    elif response.json() == []:
        return []
    elif response.json()[0]['balance'] == '0':
        return []
    utxos = response.json()
    utxos = pd.DataFrame(utxos[0]['utxo_set']).astype({'value': 'str'}).astype({'value': 'int'}).rename(columns={'tx_hash': 'TxHash', 'tx_index': 'TxIx', 'value': 'Lovelace'})
    utxos = utxos.sort_values(by=['block_time'], ascending=True)
    utxos.reset_index(drop=True, inplace=True)
    if filter_handles == True:
        utxos = hide_handles(utxos)
    if filter_assets == True:
        utxos = hide_assets(utxos)
    return utxos



def hide_assets(utxos):
    row_drop, i = [], 0
    if len(utxos) == 0:
        return utxos
    while i < len(utxos):
        asset_list = utxos['asset_list'][i]
        if len(asset_list) != 0:
            row_drop.append(i)
        i += 1
    utxos.drop(utxos.loc[row_drop].index, inplace=True)
    utxos.reset_index(drop=True, inplace=True)
    return utxos


def hide_handles(utxos):
    row_drop, i = [], 0
    if len(utxos) == 0:
        return utxos
    while i < len(utxos):
        asset_list = utxos['asset_list'][i]
        if len(asset_list) == 1:
            if asset_list[0]['policy_id'] == handle_policy:
                row_drop.append(i)
        i += 1
    utxos.drop(utxos.loc[row_drop].index, inplace=True)
    utxos.reset_index(drop=True, inplace=True)
    return utxos




def check_royalty_info(policy_id, api_base_url):
    first_mint, royalty, fingerprint = False, None, get_asset_fingerprint(policy_id, '')
    headers = {'Accept': 'application/json'}
    response = requests.get(f'{api_base_url}/asset_policy_info?_asset_policy={policy_id}', headers=headers, timeout=30)
    status = response.status_code
    response = response.json()
    if status == 200 and len(response) != 0:
        first_mint = True
        if response[0]['fingerprint'] == fingerprint:
            if 'minting_tx_metadata' in response[0]:
                if response[0]['minting_tx_metadata']['key'] == '777':
                    royalty = response[0]['minting_tx_metadata']['json']
    return first_mint, royalty




def submit_tx_api(cbor_file, api_base_url):
    status, attempts = None, 0
    headers = {'Content-Type': 'application/cbor'}
    while True:
        if attempts >= 4:
            return status
        try:
            response = requests.post(f'{api_base_url}/submittx', headers=headers, data=cbor_file, timeout=25)
        except:
            sleep(.2)
            attempts += 1
            continue
        if response.status_code == 202:
            status = response.json()
            break
        sleep(.2)
        attempts += 1
    return status

#
def check_tx_status(tx_id, api_base_url):
    sleep(.2)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_tx_hashes":["{tx_id}"]\u007d'
    response = requests.post(f'{api_base_url}/tx_status', headers=headers, data=data, timeout=10)
    if response.status_code == 200:
        status = response.json()
        confirmations = status[0]['num_confirmations']
    else:
        confirmations = None
    return confirmations


def wallet_stake_from_handle(ada_handle, api_base_url):
    asset_name = ada_handle[1:]
    wallet_addr, stake_addr = get_asset_owner(handle_policy, asset_name, api_base_url)
    return wallet_addr, stake_addr


def get_asset_owner(policy_id, asset_name, api_base_url):
    sleep(.2)
    hex_name = name_2_hex(asset_name)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    response = requests.get(f'{api_base_url}/asset_address_list?_asset_policy={policy_id}&_asset_name={hex_name}', headers=headers, timeout=10)
    if not response.ok or len(response.json()) == 0:
        return None, None
    wallet_addr = response.json()[0]['payment_address']
    stake_addr = wallet_to_stake(wallet_addr, api_base_url)
    return wallet_addr, stake_addr


def multi_wallet_utxos(mainnet_wallet, testnets_wallet):
    mainnet_utxos = get_utxos(mainnet_wallet, set_correct_api('mainnet'))
    preprod_utxos = get_utxos(testnets_wallet, set_correct_api('preprod'))
    preview_utxos = get_utxos(testnets_wallet, set_correct_api('preview'))
    if len(mainnet_utxos) == 0 and len(preprod_utxos) == 0 and len(preview_utxos) == 0:
        return []
    utxos = pd.DataFrame(data=None, index=None)
    if len(mainnet_utxos) != 0 and type(mainnet_utxos) != str:
        i = 0
        while i < len(mainnet_utxos):
            tx_hash, tx_ix, asset_list, ll_in = mainnet_utxos['TxHash'][i], mainnet_utxos['TxIx'][i], mainnet_utxos['asset_list'][i], mainnet_utxos['Lovelace'][i]
            temp_row = pd.DataFrame([[f'{tx_hash}#{tx_ix}', tx_hash, tx_ix, asset_list, ll_in, 'mainnet']],columns=['full_utxo', 'tx_hash', 'tx_ix', 'asset_list', 'll_in', 'network'])
            utxos = pd.concat([utxos,temp_row])
            i += 1
    if len(preprod_utxos) != 0 and type(preprod_utxos) != str:
        i = 0
        while i < len(preprod_utxos):
            tx_hash, tx_ix, asset_list, ll_in = preprod_utxos['TxHash'][i], preprod_utxos['TxIx'][i], preprod_utxos['asset_list'][i], preprod_utxos['Lovelace'][i]
            temp_row = pd.DataFrame([[f'{tx_hash}#{tx_ix}', tx_hash, tx_ix, asset_list, ll_in, 'preprod']],columns=['full_utxo', 'tx_hash', 'tx_ix', 'asset_list', 'll_in', 'network'])
            utxos = pd.concat([utxos, temp_row])
            i += 1
    if len(preview_utxos) != 0 and type(preview_utxos) != str:
        i = 0
        while i < len(preview_utxos):
            tx_hash, tx_ix, asset_list, ll_in = preview_utxos['TxHash'][i], preview_utxos['TxIx'][i], preview_utxos['asset_list'][i], preview_utxos['Lovelace'][i]
            temp_row = pd.DataFrame([[f'{tx_hash}#{tx_ix}', tx_hash, tx_ix, asset_list, ll_in, 'preview']],columns=['full_utxo', 'tx_hash', 'tx_ix', 'asset_list', 'll_in', 'network'])
            utxos = pd.concat([utxos,temp_row])
            i += 1
    utxos.reset_index(drop=True, inplace=True)
    return utxos

def set_correct_api(network):
    mainnet_api, preprod_api, preview_api = 'https://api.koios.rest/api/v0', 'https://preprod.koios.rest/api/v0', 'https://preview.koios.rest/api/v0'
    if network == 'mainnet':
        api_base_url = mainnet_api
    elif network == 'preprod':
        api_base_url = preprod_api
    elif network == 'preview':
        api_base_url = preview_api
    return api_base_url


def get_last_block(api_base_url):
    headers = {'Accept': 'application/json'}
    response = requests.get(f'{api_base_url}/tip', headers=headers, timeout=10)
    if response.status_code != 200:
        return None
    return response.json()[0]['hash']