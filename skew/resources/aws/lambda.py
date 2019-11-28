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

import logging
import jmespath
from skew.resources.aws import AWSResource


LOG = logging.getLogger(__name__)


class Function(AWSResource):
    def __init__(self, client, data, query=None):
        super(Function, self).__init__(client, data, query)
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
                    data = jmespath.search(detail_path, data)
                if data != None and 'ResponseMetadata' in data:
                    del data['ResponseMetadata']
                self.data[detail_key] = data
                LOG.debug(data)

    @classmethod
    def enumerate(cls, arn, region, account, resource_id=None, **kwargs):
        resources = super(Function, cls).enumerate(arn, region, account,
                                                   resource_id, **kwargs)
        for r in resources:
            r.data['EventSources'] = []
            kwargs = {'FunctionName': r.data['FunctionName']}
            response = r._client.call('list_event_source_mappings', **kwargs)
            for esm in response['EventSourceMappings']:
                r.data['EventSources'].append(esm['EventSourceArn'])
        return resources
    
   
    def shutdown(self):
        args = {
            "FunctionName": self.id,
            "ReservedConcurrentExecutions": 0
        }
        count =jmespath.search("Concurrency.ReservedConcurrentExecutions", self.data)
        if count == None or count > 0:
            return self._client.call("put_function_concurrency",**args)
        return None
       


    class Meta(object):
        service = 'lambda'
        type = 'function'
        enum_spec = ('list_functions', 'Functions', None)
        attr_required = True
        attr_spec = [
            ('get_function', 'FunctionName',
                'Concurrency', 'Concurrency')
        ]

        detail_spec = None
        id = 'FunctionName'
        filter_name = None
        name = 'FunctionName'
        date = 'LastModified'
        dimension = 'FunctionName'
        tags_spec = ('list_tags', 'Tags','Resource', 'arn')

    @classmethod
    def filter(cls, arn, resource_id, data):
        function_name = data.get(cls.Meta.id)
        LOG.debug('%s == %s', resource_id, function_name)
        return resource_id == function_name

    @property
    def arn(self):
        return self.data.get('FunctionArn')
