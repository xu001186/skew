import logging
import jmespath
from skew.resources.aws import AWSResource


LOG = logging.getLogger(__name__)


class CloudfrontResource(AWSResource):

    def __init__(self, client, data, query=None):
        super(CloudfrontResource, self).__init__(client, data, query)
        self._data = data
        self._keys = []
        self._id = data[self.Meta.id]
        # add addition attribute data
        if self.Meta.attr_required:
            for attr in self.Meta.attr_spec:
                LOG.debug(attr)
                detail_op, param_name, detail_path, detail_key = attr
                params = {param_name: self._id}
                data = self._client.call(detail_op, **params)
                if not (detail_path is None):
                    config_data = jmespath.search(detail_path, data)
                    if "Id" in config_data:
                        del config_data['id']
                    if ("ETag" in data):
                        self.data["ETag"] = data["ETag"]
                if data != None and 'ResponseMetadata' in data:
                    del data['ResponseMetadata']
                self.data[detail_key] = config_data
                LOG.debug(data)

    @property
    def arn(self):

        return 'arn:aws:%s::%s:%s/%s' % (
            self._client.service_name,
            self._client.account_id, self.resourcetype, self.id)



class Distribution(CloudfrontResource):
    
    def shutdown(self):
        if jmespath.search("Distribution_Config.Enabled", self.data) != True:
            return None

        args = {
            "Id": self.id,
        }
        if "ETag" in self.data:
            args["IfMatch"] = self.data["ETag"]
        previous_config = self.data["Distribution_Config"]
        previous_config["Enabled"] = False
        args["DistributionConfig"] = previous_config
        return self._client.call("update_distribution",**args)

    class Meta(object):
        service = 'cloudfront'
        type = 'distribution'
        enum_spec = ('list_distributions', 'DistributionList.Items[]', None)
        detail_spec = None
        id = 'Id'
        tags_spec = ('list_tags_for_resource', 'Tags.Items[]',
                     'Resource', 'arn')

        attr_required = True
        attr_spec = [
            ('get_distribution_config', 'Id',
                'DistributionConfig', 'Distribution_Config')
        ]
        name = 'DomainName'
        filter_name = None
        date = 'LastModifiedTime'
        dimension = None

    @classmethod
    def filter(cls, arn, resource_id, data):
        LOG.debug('%s == %s', resource_id, data)
        return resource_id == data['Id']
