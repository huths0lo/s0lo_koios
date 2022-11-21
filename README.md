# s0lo_koios

A simple python module for interacting with the Koios API.  It is designed to work with each of the networks supported by Koios.  As such each function requires that you send the API URL along with the additional information relevant to the function.  The recommend usage for the API URL is as follows:

api_network = 'api' # Use 'api' for Mainnet, 'preview' for Preview, 'preprod' for Preprod, and 'guild' for Guild.
api_base_url = f'https://{api_network}.koios.rest/api/v0'


Functions in Modue:
1) get_sender_address
  Requires the tx hash from a transaction, and provides back the wallet address that the transaction came from
2) get_first_used_address
  Requires a stake key, and returns the first wallet address used by that stake account.  This query is designed to defeat a person from spoofing someone elses account with a franken address, and is used with "The Morphium" to send the asset back to, regardless of which wallet address the transaciton came from.
3) get_pool_info
  Requires a bech32 pool id, and returns the specifications for the given pool.
4) get_delegate_info
  Requires a stake key, and returns the staking accounts delegation info
5) get_pool_delegates
  Requires a bech32 pool id, and optionally the epoch you want to query for.  If no epoch is provided, it will first determine the current epoch before running.
6) get_epoch_tip
  No additional info needed  Provides bak the current epoch, and the current tip.
7) get_wallet_assets
  Requires a stake key.  Returns all assets currently on all wallet addresses that are part of the stake key.
8) get_epoch_params
  Optionally uses an epoch number to get that epochs info.  Returns the paramaeters currently in use.
9) check_fungible_tag
  Used internally within "The Morphium" to identify distinct tranasactions
10) get_cardano_price
  This query doesnt use koios, but is handy in identifying the current ada to usd value.  You can optionally replace the last tag on the end of line 197 for your local currency (ie cad, gbp, aud, etc)
11) submit_tx_api
  Requires a binary enconded transaction file.  This is used to submit a signed transaction to the blockchain.  I beleive this is the same endpoing that Eternl Wallet is currently using.
12) wallet_stake_from_handle
  requires the ascii token name from an ada handle.  Returns the current wallet address, and stake address the handle is in.
13) get_asset_owner
  Requires a policy id, and ascii token name.  Returns the current wallet address and stake address that asset sits in.
