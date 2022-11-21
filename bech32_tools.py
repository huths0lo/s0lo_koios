import bech32
import binascii
from hashlib import blake2b





def scriptPubKey_2_mainnet(scriptPubKey):
    spk = binascii.unhexlify(scriptPubKey)
    version = spk[0] - 0x50 if spk[0] else 0
    program = spk[2:]
    return bech32.encode('bc', version, program)


def get_asset_fingerprint(policy_id, hex_id):
    binary_asset = binascii.unhexlify(policy_id + hex_id)
    hexstr = blake2b(binary_asset, digest_size=20).hexdigest()
    encodedstr = bech32.bech32_encode("asset",bech32.convertbits(bytes.fromhex(hexstr), 8, 5))
    return encodedstr

def wallet_to_stake(wallet_addr, api_base_url):
    if len(wallet_addr) < 64:
        return wallet_addr
    if api_base_url == 'https://api.koios.rest/api/v0':
        header = binary_2_hex('11100001')[2:]
        prefix = 'stake'
    else:
        header = binary_2_hex('11100000')[2:]
        prefix = 'stake_'
    address_words = bech32.bech32_decode(wallet_addr)
    address_hexlist = bech32.convertbits(address_words[1], 5, 16)
    account = ''.join([f'{c:04x}' for c in address_hexlist])[-58:-2]
    btr = bytes.fromhex(header + account)
    stake_words = bech32.convertbits(btr, 8, 5)
    stake_addr = bech32.bech32_encode(prefix, stake_words)
    return stake_addr

def binary_2_hex(binary_str):
    decimal_value = int(binary_str, 2)
    hex_value = hex(decimal_value)
    return hex_value
