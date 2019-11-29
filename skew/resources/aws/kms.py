# Copyright (c) 2014 Scopely, Inc.
# Copyright (c) 2015 Mitch Garnaat
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from skew.resources.aws import AWSResource
import jmespath

class Key(AWSResource):

    def __init__(self, client, data, query=None):
        super(Key, self).__init__(client, data, query)
        self._data = data
        self._keys = []
        self._id = data[self.Meta.id]
        if self.Meta.attr_required:
            for attr in self.Meta.attr_spec:
                detail_op, param_name, detail_path, detail_key = attr
                params = {param_name: self._id}
                data = self._client.call(detail_op, **params)
                if not (detail_path is None):
                    config_data = jmespath.search(detail_path, data)
                if data != None and 'ResponseMetadata' in data:
                    del data['ResponseMetadata']
                self.data[detail_key] = config_data

    class Meta(object):
        service = 'kms'
        type = 'key'
        attr_required = True
        attr_spec = [
            ('list_aliases', 'KeyId',
                'Aliases', 'Aliases')
        ]
        enum_spec = ('list_keys', 'Keys', None)
        tags_spec = ('list_resource_tags', 'Tags',
                     'KeyId', 'id')
        detail_spec = None
        id = 'KeyId'
        filter_name = None
        filter_type = None
        name = 'KeyId'
        date = None
        dimension = None

    @classmethod
    def filter(cls, arn, resource_id, data):
        return resource_id == data['KeyId']

    def shutdown(self):
        args = {
            "KeyId": self.id
        }
        shutdown_continue = True
        for alias in self.data["Aliases"]:
            if alias["AliasName"].startswith("alias/aws"):
                shutdown_continue = False
        if  shutdown_continue:
            return self._client.call("disable_key",**args)
        return None
       

    @property
    def tags(self):
        if self._tags is None:
            self._tags = {}

            if hasattr(self.Meta, 'tags_spec') and (self.Meta.tags_spec is not None):
                
                method, path, param_name, param_value = self.Meta.tags_spec[:4]
                kwargs = {}
                filter_type = getattr(self.Meta, 'filter_type', None)
                if filter_type == 'arn':
                    kwargs = {param_name: [getattr(self, param_value)]}
                elif filter_type == 'list':
                    kwargs = {param_name: [getattr(self, param_value)]}
                else:
                    kwargs = {param_name: getattr(self, param_value)}
                if len(self.Meta.tags_spec) > 4:
                    kwargs.update(self.Meta.tags_spec[4])
                self.data['Tags'] = self._client.call(
                    method, query=path, **kwargs)
       
            if 'Tags' in self.data:
                _tags = self.data['Tags']
                if isinstance(_tags, list):
                    for kvpair in _tags:
                        if kvpair['TagKey'] in self._tags:
                            if not isinstance(self._tags[kvpair['TagKey']], list):
                                self._tags[kvpair['TagKey']] = [self._tags[kvpair['TagKey']]]
                            self._tags[kvpair['TagKey']].append(kvpair['TagValue'])
                        else:
                            self._tags[kvpair['TagKey']] = kvpair['TagValue']
                            
                elif isinstance(_tags, dict):
                    self._tags = _tags
        return self._tags
