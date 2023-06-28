import requests

from app.utils import ExceptionUtils
from app.utils.types import IndexerType
from config import Config
from app.indexer.client._base import _IIndexClient
from app.utils import RequestUtils
from app.helper import IndexerConf


class Jackett(_IIndexClient):
    # 索引器ID
    client_id = "jackett"
    # 索引器类型
    client_type = IndexerType.JACKETT
    # 索引器名称
    client_name = IndexerType.JACKETT.value

    # 私有属性
    _client_config = {}
    _password = None
    _api_key = None
    _host = None

    def __init__(self, config=None):
        super().__init__()
        self._client_config = config or Config().get_config('jackett')
        self.init_config()

    def init_config(self):
        if self._client_config:
            self._api_key = self._client_config.get('api_key')
            self._password = self._client_config.get('password')
            self._host = self._client_config.get('host')

            if not self._host.startswith('http'):
                self._host = "http://" + self._host
            if not self._host.endswith('/'):
                self._host = self._host + "/"

    @classmethod
    def match(cls, ctype):
        return True if ctype in [cls.client_id, cls.client_type, cls.client_name] else False

    def get_type(self):
        return self.client_type

    def get_status(self):
        """
        检查连通性
        :return: True、False
        """
        if not self._api_key or not self._host:
            return False
        return True if self.get_indexers() else False

    def get_indexers(self):
        """
        获取配置的jackett indexer
        :return: indexer 信息 [(indexerId, indexerName, url)]
        """
        # 获取Cookie
        cookie = None
        session = requests.session()
        res = RequestUtils(session=session).post_res(url=f"{self._host}UI/Dashboard",params={"password": self._password})
        if res and session.cookies:
            cookie = session.cookies.get_dict()
        indexer_query_url = f"{self._host}api/v2.0/indexers?configured=true"
        try:
            ret = RequestUtils(cookies=cookie).get_res(indexer_query_url)
            if not ret or not ret.json():
                return []
            return [IndexerConf({"id": v["id"],
                                 "name": v["name"],
                                 "domain": f'{self._host}api/v2.0/indexers/{v["id"]}/results/torznab/',
                                 "public": True if v['type'] == 'public' else False,
                                 "builtin": False})
                    for v in ret.json()]
        except Exception as e2:
            ExceptionUtils.exception_traceback(e2)
            return []

    def search(self, *kwargs):
        return super().search(*kwargs)