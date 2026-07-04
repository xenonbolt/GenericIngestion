import ssl
import urllib3
import requests
import httpx
import warnings

def apply_global_ssl_bypass():
    """
    WARNING: This disables SSL verification globally.
    DO NOT USE IN PRODUCTION. This is strictly for restricted proxy/lab environments.
    """
    # 1. Disable urllib3 warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    # 2. Patch global ssl context
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    # 3. Patch Requests default Session to always verify=False
    old_request = requests.Session.request
    def new_request(self, method, url, **kwargs):
        kwargs['verify'] = False
        return old_request(self, method, url, **kwargs)
    requests.Session.request = new_request

    # 4. Patch HTTPX to not verify SSL
    old_httpx_init = httpx.Client.__init__
    def new_httpx_init(self, *args, **kwargs):
        kwargs['verify'] = False
        old_httpx_init(self, *args, **kwargs)
    httpx.Client.__init__ = new_httpx_init
    
    old_httpx_async_init = httpx.AsyncClient.__init__
    def new_httpx_async_init(self, *args, **kwargs):
        kwargs['verify'] = False
        old_httpx_async_init(self, *args, **kwargs)
    httpx.AsyncClient.__init__ = new_httpx_async_init

    print("⚠️  WARNING: Global SSL Verification has been disabled for Lab Environment.")

# Automatically apply upon import
apply_global_ssl_bypass()
