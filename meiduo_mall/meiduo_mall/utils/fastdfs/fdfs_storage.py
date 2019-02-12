from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from fdfs_client.client import Fdfs_client

@deconstructible
class FastDFSStorage(Storage):
    def __init__(self, base_url=None, client_conf=None):
        """

        :param base_url: 用于构造图片完整路径使用，图片服务器的域名
        :param client_conf: FastDFS客户端配置文件的路径
        """
        if base_url == None:
            base_url = settings.FDFS_URL
        self.base_url = base_url
        if client_conf == None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf


    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        client = Fdfs_client(self.client_conf)
        ret = client.upload_by_buffer(content.read())
        if ret.get('Status') != "Upload successed.":
            raise Exception("upload file failed")

        file_name = ret.get('Remote file_id')

        return file_name

    def url(self, name):
        """

        :param name: 存储到数据库中的文件名
        :return: 返回完整的图片路径
        """

        return self.base_url + name

    def exists(self, name):
        """

        :param name: 文件名
        :return: false表示文件都是新上传的
        """

        return False