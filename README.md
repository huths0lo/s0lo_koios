# s0lo_koios

A simple python module for interacting with the Koios API.  It is designed to work with each of the networks supported by Koios.  As such each function requires that you send the API URL along with the additional information relevant to the function.  The recommend usage for the API URL is as follows:

api_network = 'api' # Use 'api' for Mainnet, 'preview' for Preview, 'preprod' for Preprod, and 'guild' for Guild.
api_base_url = f'https://{api_network}.koios.rest/api/v0'


