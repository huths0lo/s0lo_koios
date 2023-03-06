import aiohttp
import pandas as pd
from common_functions import name_2_hex
from bech32_tools import wallet_to_stake, get_asset_fingerprint
import asyncio


handle_policy = 'f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a'


#async def main(url, payload=None, params=None, ):
#    async with aiohttp.ClientSession() as session:
#        pokemon_url = 'https://pokeapi.co/api/v2/pokemon/151'
#        async with session.get(pokemon_url) as resp:
#            pokemon = await resp.json()
#            print(pokemon['name'])

#session.post('http://httpbin.org/post', data=b'data')
#session.put('http://httpbin.org/put', data=b'data')
#session.delete('http://httpbin.org/delete')
#session.head('http://httpbin.org/get')
#session.options('http://httpbin.org/get')
#session.patch('http://httpbin.org/patch', data=b'data')


#sender_addr = asyncio.run(get_sender_address(tx_hash, api_base_url))



async def get_stake_utxos(stake_key, api_base_url):
    all_utxos = []
    wallet_addresses = await get_account_addresses(stake_key, api_base_url)
    if wallet_addresses == None:
        return []
    await asyncio.sleep(.1)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = f'\u007b"_addresses":['
    for wallet in wallet_addresses:
        payload += f'"{wallet}",'
    payload = payload[:len(payload) - 1]
    payload += ']\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f'{api_base_url}/address_info', headers=headers, data=payload, timeout=10) as response:
            status = response.status
            if status != 200:
                return []
            else:
                response = await response.json(content_type=None)
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






def api_base_url_from_wallet(wallet):
    if wallet[:6] == 'stake_' or wallet[:5] == 'addr_':
        api_base_url = 'https://preprod.koios.rest/api/v0'
    else:
        api_base_url = 'https://api.koios.rest/api/v0'
    return api_base_url


async def get_sender_address(tx_hash, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_tx_hashes":["{tx_hash}"]\u007d'
    print('Getting Address')
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/tx_info', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    sender_addr = response[0]['inputs'][0]['payment_addr']['bech32']
    return sender_addr



async def get_wallet_txs(wallet_addr, api_base_url, order='asc'):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_addresses":["{wallet_addr}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/address_txs?order=block_height.{order}', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return []
    return response



async def get_tx_outputs(tx_hash, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_tx_hashes":["{tx_hash}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/tx_info', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    tx_outputs = response[0]['outputs']
    return tx_outputs


async def get_first_used_address(stake_key, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"]\u007d'
    print('Getting Address')
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/account_addresses', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    first_addr = response[0]['addresses'][0]
    return first_addr



async def get_pool_info(pool_id, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_pool_bech32_ids":["{pool_id}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/pool_info', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    return response



async def get_delegate_info(stake_key, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/account_info', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    delegate_info[0]['pool_info'] = get_pool_info(response[0]['delegated_pool'], api_base_url)
    return delegate_info

async def get_account_balance(stake_key, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/account_info', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    if len(response) == 0:
        return None
    account_balance = response[0]['total_balance']
    return account_balance


async def get_delegate_by_epoch(stake_key, api_base_url, epoch):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"],"_epoch_no": {epoch}\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/account_history', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None, None
    pool_id = response[0]['history'][0]['pool_id']
    delegated = int(response[0]['history'][0]['active_stake'])
    return pool_id, delegated



async def get_pool_delegates(bech_pool_id, api_base_url, epoch=None):
    headers = {'Accept': 'application/json'}
    if epoch == None:
        epoch, tip = await get_epoch_tip(api_base_url)
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/pool_delegators_history?_pool_bech32={bech_pool_id}&_epoch_no={epoch}', headers=headers, timeout=30) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    return response



async def get_epoch_tip(api_base_url):
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/tip', headers=headers, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None, None
    epoch = int(response[0]['epoch_no'])
    tip = int(response[0]['abs_slot'])
    return epoch, tip



async def get_wallet_assets(stake_key, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_stake_addresses":["{stake_key}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/account_assets', data=data, headers=headers, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    wallet_contents = response
    return wallet_contents



async def get_epoch_params(api_base_url, epoch=None):
    if epoch == None:
        epoch, tip = await get_epoch_tip(api_base_url)
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/epoch_params?_epoch_no={epoch}', headers=headers, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    return response





async def assets_from_policy(policy_id, api_base_url):
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/asset_policy_info?_asset_policy={policy_id}', headers=headers, timeout=30) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200 or len(response) == 0:
        return None
    i, all_assets = 0, pd.DataFrame()
    while i < len(response):
        asset_name = response[i]['asset_name_ascii']
        quantity = int(response[i]['total_supply'])
        if 'minting_tx_metadata' in response[i]:
            if quantity != 0 and response[i]['minting_tx_metadata']['key'] == '721':
                temp_row = pd.DataFrame([[asset_name, quantity]], columns=['asset_name', 'quantity'])
                all_assets = pd.concat([all_assets, temp_row])
        i += 1
    all_assets.reset_index(drop=True, inplace=True)
    return all_assets



async def check_royalty_info(policy_id, api_base_url):
    first_mint, royalty, fingerprint = False, None, get_asset_fingerprint(policy_id, '')
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/asset_policy_info?_asset_policy={policy_id}', headers=headers, timeout=30) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status == 200 and len(response) != 0:
        first_mint = True
        if response[0]['fingerprint'] == fingerprint:
            if 'minting_tx_metadata' in response[0]:
                if response[0]['minting_tx_metadata']['key'] == '777':
                    royalty = response[0]['minting_tx_metadata']['json']
    return first_mint, royalty



async def check_fungible_tag(tx_hash, api_base_url):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = f'\u007b"_tx_hashes":["{tx_hash}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f'{api_base_url}/tx_metadata', headers=headers, data=payload, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    if response[0]['metadata'] != None:
        if '674' in response[0]['metadata']:
            if 'msg' in response[0]['metadata']['674']:
                if 'fungible' in response[0]['metadata']['674']['msg'].lower():
                    return True
    return False


async def get_metadata(policy_id, asset_hex, api_base_url):
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/asset_info?_asset_policy={policy_id}&_asset_name={asset_hex}', headers=headers, timeout=30) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status == 200 and len(response) != 0:
        if 'minting_tx_metadata' in response[0]:
            if '721' in response[0]['minting_tx_metadata']:
                metadata = response[0]['minting_tx_metadata']['721']
                return metadata, status
    return None, None


async def get_mint_tx(policy_id, asset_hex, api_base_url):
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/asset_info?_asset_policy={policy_id}&_asset_name={asset_hex}', headers=headers, timeout=30) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status == 200 and len(response) != 0:
        if 'minting_tx_hash' in response[0]:
            mint_tx = response[0]['minting_tx_hash']
            return mint_tx, status
    return None


async def get_cardano_price():
    cardano_price = None
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd", timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
        if status != 200:
            return None
        cardano_price = response['cardano']['usd']
    return cardano_price


async def get_utxos(wallet_address, api_base_url, filter_handles=False, filter_assets=False):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = f'\u007b"_addresses":["{wallet_address}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f'{api_base_url}/address_info', headers=headers, data=payload, timeout=10) as response:
            status = response.status
            if status != 200:
                return []
            else:
                response = await response.json(content_type=None)
    utxos = response
    if utxos[0]['balance'] == '0':
        return []
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



async def submit_tx_api(cbor_file, api_base_url):
    headers = {'Content-Type': 'application/cbor'}
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/submittx', headers=headers, data=cbor_file, timeout=10) as response:
            response = await response.json(content_type=None)
    return response



async def check_tx_status(tx_id, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_tx_hashes":["{tx_id}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/tx_status', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    return response[0]['num_confirmations']


async def get_asset_history(policy_id, asset_name, api_base_url):
    asset_url = ''
    headers = {
        'Accept': 'application/json',
    }
    if asset_name != '':
        asset_url = f'{name_2_hex(asset_name)}'
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/asset_history?_asset_policy={policy_id}&_asset_name={asset_url}', headers=headers, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200:
        return None
    return response



#



async def wallet_stake_from_handle(ada_handle, api_base_url):
    asset_name = ada_handle[1:]
    wallet_addr, stake_addr = await get_asset_owner(handle_policy, asset_name, api_base_url)
    return wallet_addr, stake_addr



async def get_asset_owner(policy_id, asset_name, api_base_url):
    hex_name = name_2_hex(asset_name)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/asset_address_list?_asset_policy={policy_id}&_asset_name={hex_name}', headers=headers, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
        if status != 200 or len(response) == 0:
            return None, None
    wallet_addr = response[0]['payment_address']
    stake_addr = wallet_to_stake(wallet_addr, api_base_url)
    return wallet_addr, stake_addr



async def get_account_addresses(stake_addr, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_stake_addresses":["{stake_addr}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/account_addresses', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200 or len(response) == 0:
        return []
    return response[0]['addresses']



async def get_required_utxos(stake_key, api_base_url, ll_needed, fungibles_needed, shuffle=False):
    if len(fungibles_needed) == 0:
        needed_asset, needed_qty = None, 0
    else:
        needed_asset, needed_qty = fungibles_needed[0][0], fungibles_needed[0][1]
    utxos_to_use, all_assets, i, ll_stored, multi_stored = [], [], 0, 0, 0
    all_addresses = await get_account_addresses(stake_key, api_base_url)
    if all_addresses == None:
        return None, None, None, None
    if shuffle:
        import random
        random.shuffle(all_addresses)
    while i < len(all_addresses):
        address_utxos = await get_utxos(all_addresses[i], api_base_url)
        if len(address_utxos) == 0:
            i += 1
            continue
        u = 0
        address_utxos = address_utxos.sort_values(['Lovelace'], ascending=False)
        address_utxos.reset_index(drop=True, inplace=True)
        while u < len(address_utxos):
            if ll_stored >= ll_needed and multi_stored >= needed_qty:
                break
            tx_hash, tx_ix, assets_in_utxo = address_utxos['TxHash'][u], address_utxos['TxIx'][u], address_utxos['asset_list'][u]
            ll_stored += address_utxos['Lovelace'][u]
            utxos_to_use.append([tx_hash, int(tx_ix)])
            if len(assets_in_utxo) != 0:
                all_assets.append(assets_in_utxo)
            if needed_asset != None:
                policy_id, asset_name = needed_asset[:56], needed_asset[57:]
                for each_asset in assets_in_utxo:
                    if policy_id.lower() == each_asset['policy_id'].lower() and asset_name.lower() == each_asset['asset_name'].lower():
                        multi_stored += int(each_asset['quantity'])
            if ll_stored >= ll_needed and multi_stored >= needed_qty:
                break
            u += 1
        i += 1
    if ll_stored < ll_needed or multi_stored < needed_qty:
        return None, None, None, None
    return utxos_to_use, all_assets, int(ll_stored), int(multi_stored)


async def staking_wallets_utxos(stake_addr, api_base_url):
    all_addresses = await get_account_addresses(stake_addr, api_base_url)
    if all_addresses == None:
        return []
    utxos = pd.DataFrame(data=None, index=None)
    for address in all_addresses:
        address_utxos = await get_utxos(address, api_base_url)
        if len(address_utxos) != 0:
            utxos = pd.concat([utxos, address_utxos])
    utxos.reset_index(drop=True, inplace=True)
    return utxos


async def multi_wallet_utxos(mainnet_wallet, testnets_wallet):
    mainnet_utxos = await get_utxos(mainnet_wallet, set_correct_api('mainnet'))
    preprod_utxos = await get_utxos(testnets_wallet, set_correct_api('preprod'))
    preview_utxos = await get_utxos(testnets_wallet, set_correct_api('preview'))
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


async def get_last_block(api_base_url):
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_base_url}/tip', headers=headers, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
        if status != 200:
            return None
    return response[0]['hash']



async def get_script_datum(datum_hash, api_base_url):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = f'\u007b"_datum_hashes":["{datum_hash}"]\u007d'
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_base_url}/datum_info', headers=headers, data=data, timeout=10) as response:
            status = response.status
            response = await response.json(content_type=None)
    if status != 200 or len(response) == 0:
        return []
    return response



#api_base_url = 'https://api.koios.rest/api/v0'