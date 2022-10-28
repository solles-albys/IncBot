import asyncio
import json
import ssl
from enum import Enum
from typing import Coroutine

import aiohttp
from lib.logger import get_logger, loglevel_gt_debug

_logger = get_logger('http-client')

_ssl_context = None


def load_ca_certificate(cert_filename):
    """Load CA certificate from the file."""
    global _ssl_context
    if not cert_filename:
        return

    _ssl_context = ssl.SSLContext()
    _ssl_context.load_verify_locations(cert_filename)


class Params(dict):
    """Params is a dict without empty values."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self[k] = v  # __setitem__

    def __setitem__(self, key, value):
        if value is None or value == '':
            return
        super().__setitem__(key, value)


class HttpAuth(Enum):
    NONE = 0
    BASIC_AUTH = 1


class BaseClient:
    base_url: str = None
    total_timeout: float = 30.
    connect_timeout: float = 1.
    read_sock_timeout: float = 30.
    connect_sock_timeout: float = 1.
    headers: dict[str, str] = None
    raise_for_status: bool = True
    
    auth_type: HttpAuth = HttpAuth.NONE
    basic_auth_username: str = None
    basic_auth_password: str = None
    
    max_retries: int = 1
    wait_before_next_retry_seconds: tuple[float, ...] | float = 1.0
    
    
    def __init__(self, *, 
                 base_url: str = None,
                 total_timeout: float = None,
                 connect_timeout: float = None,
                 read_sock_timeout: float = None,
                 connect_sock_timeout: float = None,
                 headers: dict[str, str] = None,
                 raise_for_status: bool = None, 
                 basic_auth_username: str = None,
                 basic_auth_password: str = None,
                 ):
        self._session: aiohttp.ClientSession = None
        
        self.base_url = base_url or self.__class__.base_url
        self.total_timeout = total_timeout or self.__class__.total_timeout
        self.connect_timeout = connect_timeout or self.__class__.connect_timeout
        self.read_sock_timeout = read_sock_timeout or self.__class__.read_sock_timeout
        self.connect_sock_timeout = connect_sock_timeout or self.__class__.connect_sock_timeout
        self.headers = headers or self.__class__.headers or dict()
        self.raise_for_status = raise_for_status or self.__class__.raise_for_status

        self.basic_auth_username: str = basic_auth_username or self.__class__.basic_auth_username
        self.basic_auth_password: str = basic_auth_password or self.__class__.basic_auth_password
    
    async def get(self, url, *, allow_redirects=True, **kwargs) -> aiohttp.ClientResponse:
        return await self.request('get', url, 
                                  allow_redirects=allow_redirects, 
                                  **kwargs)
    
    async def post(self, url, *, allow_redirects=True, **kwargs) -> aiohttp.ClientResponse:
        return await self.request('post', url,
                                  allow_redirects=allow_redirects,
                                  **kwargs)
    
    async def delete(self, url, *, allow_redirects=True, **kwargs) -> aiohttp.ClientResponse:
        return await self.request('delete', url,
                                  allow_redirects=allow_redirects,
                                  **kwargs)
    
    async def patch(self, url, *, allow_redirects=True, **kwargs) -> aiohttp.ClientResponse:
        return await self.request('patch', url,
                                  allow_redirects=allow_redirects,
                                  **kwargs)
    
    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        headers = self.headers.copy()
        headers.update(kwargs.get('headers', {}))
        kwargs['headers'] = headers
        
        retry_count = 0
        last_exc = None
        while retry_count <= self.max_retries:
            status = 0
            try:
                _raise_for_status = kwargs.pop('raise_for_status', self.raise_for_status)
                response = await self._request(method, url, **kwargs)
                status = response.status
                
                if _raise_for_status:
                    response.raise_for_status()
                
                return response
            except Exception as e:
                last_exc = e
                if status % 100 == 4:
                    raise e
                
                if isinstance(self.wait_before_next_retry_seconds, tuple):
                    current_wait_index = retry_count if retry_count < len(self.wait_before_next_retry_seconds) else -1
                    retry_wait = self.wait_before_next_retry_seconds[current_wait_index]
                else:
                    retry_wait = self.wait_before_next_retry_seconds
                
                retry_count += 1
                # TODO: log error
                await asyncio.sleep(retry_wait)
        
        if last_exc is not None:
            raise last_exc

    async def _request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        skip_log = loglevel_gt_debug()
        if not skip_log:
            logger = _logger.with_fields(method=method, url=url, params=str(kwargs.get('params')))
        
        if not self._session:
            self._session = self._create_session(
                timeout=aiohttp.ClientTimeout(
                    total=self.total_timeout,
                    connect=self.connect_timeout,
                    sock_read=self.read_sock_timeout,
                    sock_connect=self.connect_sock_timeout,  
                ),
            )
        
        if self.base_url:
            url = f'{self.base_url}{url}'

        async with self._session.request(method, url, **kwargs) as response:
            # Read response body to use after closed connection.
            read_bytes = await response.read()
            
            if not skip_log:
                logger.debug('request', status=response.status)
            
            async def read():
                return read_bytes
            
            # hack
            response.read = read
            return response

    def _create_session(self, **kwargs) -> aiohttp.ClientSession:
        """Return a new client session. Override in subclasses to customize
        session."""
        global _ssl_context
        if _ssl_context:
            kwargs.setdefault('connector',
                              aiohttp.TCPConnector(ssl_context=_ssl_context))

        kwargs.setdefault('json_serialize', json.dumps)
        
        if self.auth_type == HttpAuth.BASIC_AUTH:
            kwargs['auth'] = aiohttp.BasicAuth(login=self.basic_auth_username, password=self.basic_auth_password)
        
        return aiohttp.ClientSession(**kwargs)
    
    async def close(self) -> Coroutine:
        if self._session:
            return self._session.close()
    
    