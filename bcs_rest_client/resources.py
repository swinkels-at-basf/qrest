import requests
import copy
import six
from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)

from .exception import BCSRestResourceHTTPError, BCSRestResourceMissingContentError

if six.PY2:
    from urllib import quote
elif six.PY3:
    from urllib.parse import quote
else:
    raise Exception('gvd')
    


#local imports
from .utils import URLValidator
from .utils import contract

@contract
def validate_resources_configuration(config_dict):
    """ Validates a resources configuration and raises appropriate exceptions

        :param config_dict: The object that represents the REST API resources
        :type config_dict: ``dict``
    """
    for resource_name, resource_config in config_dict.items():
        if not isinstance(resource_name, six.string_types):
            raise ValueError("resource name '{resource}' is not a string".format(
                resource=resource_name
            ))
        if resource_name == 'data':
            raise ValueError("resource name may not be named 'data'")
        if not isinstance(resource_config, dict):
            raise ValueError("resource name '{resource}' value is not a dictionary".format(
                resource=resource_name
            ))
        
        # path configuration
        if "path" in resource_config:
            if not isinstance(resource_config["path"], list):
                raise ValueError("path for resource '{resource}' is not a list".format(
                    resource=resource_name
                ))
            for part in resource_config["path"]:
                if not isinstance(part, six.string_types):
                    raise ValueError("part '{part}' of path for resource '{resource}' is not a string".format(
                        resource=resource_name,
                        part=part
                    ))
                #elif part == "{data}":
                    #raise SyntaxError("'data' isn't a valid path parameter name for resource '{resource}'".format(
                        #resource=resource_name
                    #))

        # method
        if "method" in resource_config:
            if not isinstance(resource_config["method"], six.string_types):
                raise ValueError("method for resource '{resource}' is not a string".format(
                    resource=resource_name
                ))
            elif resource_config["method"] not in ['GET', 'POST']:
                raise ValueError("method for resource '{resource}' must be GET or POST".format(
                    resource=resource_name
                ))
        else:
            raise ValueError("method for resource '{resource}' is missing".format(
                resource=resource_name
            ))

        # query parameters
        if "query_parameters" in resource_config:
            if not isinstance(resource_config["query_parameters"], list):
                raise ValueError("query parameters for resource '{resource}' is not a list".format(
                    resource=resource_name
                ))
            if not resource_config["query_parameters"]:
                raise ValueError("query parameters for resource '{resource}' is empty".format(
                    resource=resource_name
                ))
            for parameter in resource_config["query_parameters"]:
                if not isinstance(parameter, dict):
                    raise ValueError("not all query parameters for resource '{resource}' are a dictionary".format(
                        resource=resource_name
                    ))
                if "name" in parameter:
                    if not isinstance(parameter["name"], six.string_types):
                        raise ValueError("not all query parameter names for resource '{resource}' are a string".format(
                            resource=resource_name
                        ))
                    #elif parameter["name"] == "data":
                        #raise SyntaxError("'data' isn't a valid query parameter name for resource '{resource}'".format(
                            #resource=resource_name
                        #))
                else:
                    raise SyntaxError("not all query parameters for resource '{resource}' have a name".format(
                        resource=resource_name
                    ))
                if "group" in parameter:
                    if not isinstance(parameter["group"], six.string_types):
                        raise ValueError("not all query parameter group names for resource '{resource}' are a string".format(
                            resource=resource_name
                        ))
                if "required" in parameter:
                    if not isinstance(parameter["required"], bool):
                        raise ValueError("not all query parameter 'required' options for resource '{resource}' are a boolean".format(
                            resource=resource_name
                        ))
                if "multiple" in parameter:
                    if not isinstance(parameter["multiple"], bool):
                        raise ValueError("not all query parameter 'multiple' options for resource '{resource}' are a boolean".format(
                            resource=resource_name
                        ))
        # json
        if "json" in resource_config:
            if not isinstance(resource_config["json"], dict):
                raise ValueError("json option for resource '{resource}' is not a dictionary".format(
                    resource=resource_name
                ))
            if "root" in resource_config["json"]:
                if not isinstance(resource_config["json"]["root"], list):
                    raise ValueError("json.root option for resource '{resource}' is not a list".format(
                        resource=resource_name
                    ))
                for key in resource_config["json"]["root"]:
                    if not isinstance(key, six.string_types):
                        raise ValueError("json.root list element {key} for resource '{resource}' is not a string".format(
                            resource=resource_name,
                            key=key
                        ))
            if "source_name" in resource_config["json"]:
                if not isinstance(resource_config["json"]["source_name"], six.string_types):
                    raise ValueError("json.source_name option for resource '{resource}' is not a string".format(
                        resource=resource_name
                    ))
            if "result_name" in resource_config["json"]:
                if not isinstance(resource_config["json"]["result_name"], six.string_types):
                    raise ValueError("json.result_name option for resource '{resource}' is not a string".format(
                        resource=resource_name
                    ))


class RestResponse(object):
    '''
    Wrapper around the REST response. This is meant to process the response coming from the requests
    call into a python object
    '''

    def __init__(self, response, options={}):
        """ RestResponse constructor

            :param response: The Requests Response object

            :param options: The options object specifying the JSON options for returning results
            :type options: ``dict``

        """
        assert isinstance(response, requests.models.Response)
        self._response = response
        #self._response.raise_for_status()
        self.headers = response.headers
        self.content = response.content
        self.options = options

        #prepare the content to a python object
        self.data = None
        self._to_python()
        
    @property
    def response_type(self):
        """ Checks whether the Requests Response object contains JSON or not

            :return: True when the Requests Response object contains JSON and False when it does not
            :rtype: ``bool``
        """
        
        content_type = self.headers.get('content-type', None)
        
        if "json" in content_type:
            return 'json'
        elif 'text/csv' in content_type:
            return 'csv'
        else:
            return 'unknown'

    def _parse_json_response(self):
        """ Returns the JSON contained in the Requests Response object, following the options specified in the JSON configuration

            :return: A dictionary containing the Requests Response object, adapted to the JSON configuration
            :rtype: ``dict``
        """
        json = copy.deepcopy(self._response.json())
        json_source = copy.deepcopy(self._response.json())

        result_name = self.options.get("result_name", "result")
        
        #subset the response dictionary
        if isinstance(json, dict):
            if ("root" in self.options) and (len(self.options["root"]) > 0):
                for element in self.options["root"]:
                    if element in json:
                        json = json[element]
                    else:
                        raise BCSRestResourceMissingContentError("Element '%s' could not be found" % element)
        
        # look into the subset JSON: stick it into the self object
        if not isinstance(json, dict):
            json_dict = {}
            json_dict[result_name] = json
        else:
            json_dict = json
            
        # 
        if ("root" in self.options) and (len(self.options["root"]) > 0):
            if "source_name" in self.options:
                json_dict[self.options["source_name"]] = json_source
            elif "source" not in json_dict:
                json_dict["source"] = json_source
            else:
                json_dict["_source"] = json_source
                
        # replace content by decoded content
        self.content = json_source

        #create data objects
        self.data = json_dict
        setattr(self, result_name, json)
        
    def _parse_csv_response(self):
        '''
        processes a raw CSV into lines. For very large content this may be better served by a generator
        
        : return:  a list of lists
        '''
        data = self._response.content
        self.content = data.decode('UTF-8')
        data = self.content.strip().split('\n')
        self.data = [x.split(",") for x in data]

    def _to_python(self):
        """ Returns the response body content contained in the Requests Response object.
            If the content is JSON, then the JSON content is returned adapted to the JSON configuration.
            If the content is not JSON, then the raw response body content is returned (in bytes).

            :return: A dictionary containing the response body JSON content, adapted to the JSON configuration or the raw response body content in bytes if it is not JSON
        """
        if self.response_type == 'json':
            self._parse_json_response()
        elif self.response_type == 'csv':
            self._parse_csv_response()
        




class ResourceParameters():
    '''
    Wrapper for the parameter handling, this allows the RestResource to focus on the execution
    Code here is collected from multiple location, it hasnt been refactored but shows the redundancy
    in the original code.
    
    :param list path_parameters: all parameters that end up in the url of the request
    :param dict query_parameters: Lists the required and optional query parameters for the specified REST API resource.
    :param dict query_parameter_groups: A dictionary of the different groups (key) of query parameters (value, is list) for the specified REST API resource
    '''
    
    def __init__(self, config, default):
        '''
        loads a config file and extract information in specific data structures
        '''
        self.config = self._apply_default(config, default)
        
        # although all functions below are properties, it may be more CPU friendly to 
        # store the result locally instead.
        
        self.path = config['path']
        self.method = config['method']
        self.json_options = config.get('json', {})
        self.headers = config.get('headers', {})
        self.path_parameters = self._path_parameters
        self.query_parameters = self._query_parameters
        self.query_parameter_groups = self._query_parameter_groups


    # --------------------------------------------------------------------------------------------
    @staticmethod
    def _apply_default(config, default):
        '''
        create a combined object that includes default configurations. For internal use.
        Note that this default only provides functionality for
        * method
        * headers
        * json
        '''

        # check
        allowed_default = ['headers', 'json']
        if not isinstance(default, dict):
            raise ValueError('default must be a dictionary')
        
        if set(default.keys()) - set(allowed_default):
            raise ValueError('default config may only contain %s' % ', '.join(allowed_default))

        # apply defaults
        if 'method' in default and not 'method' in config:
            config['method'] = default['method']
        if 'headers' in default:
            def_head = default['headers'].copy()
            if 'headers' in config:
                def_head.update(config['headers'])
            config['headers'] = def_head
        if 'json' in default:
            def_json = default['json'].copy()
            if 'json' in config:
                def_json.update(config['json'])
            config['json'] = def_json

        return config
        

    # --------------------------------------------------------------------------------------------
    @property
    @contract
    def multiple_parameters(self):
        """ Returns all parameters that can be used simultaneously

            :return: A list of parameters
            :rtype: ``list``
        """
        return self.query_parameters["multiple"]

    # --------------------------------------------------------------------------------------------
    @property
    @contract
    def all_parameters(self):
        """ Aggregates all parameters into a single structure

            :return: A list of parameters
            :rtype: ``list``
        """
        all_parameters = self.all_query_parameters + self.path_parameters
        return all_parameters

    # ---------------------------------------------------------------------------------------------
    @property
    @contract
    def as_dict(self):
        """ show all parameters in path or query

            :return: A dictionary that contains required and optional parameters.
            :rtype: ``dict``
        """

        # TODO: show that a parameter is a list/multiple?
        result = {"required": [], "optional": []}
        result["required"].extend(self.path_parameters)
        result["required"].extend(self.query_parameters["required"])
        result["optional"].extend(self.query_parameters["optional"])
        
        return result

    # --------------------------------------------------------------------------------------------
    @property
    @contract
    def required_parameters(self):
        """ Lists the required parameters for the specified REST API resource.
            Also summarises the query parameters that can be multiple.

            :return: A dictionary of the 'optional', 'required' and 'multiple' (keys) query parameters (value, a list) for the specified REST API resource
            :rtype: ``list``
        """
        return self.path_parameters + self.query_parameters["required"]

    # --------------------------------------------------------------------------------------------
    @property
    @contract
    def all_query_parameters(self):
        """ Lists the required and optional query parameters for the specified REST API resource.
            Also summarises the query parameters that can be multiple.

            :return: A list of parameters
            :rtype: ``list``
        """
        return self.query_parameters["optional"] + self.query_parameters["required"]


    # ---------------------------------------------------------------------------------------------
    @property
    @contract
    def _query_parameters(self):
        """ Lists the required and optional query parameters for the specified REST API resource.
            Also summarises the query parameters that can be multiple.

            :return: A dictionary of the 'optional', 'required' and 'multiple' (keys) query parameters (value, a list) for the specified REST API resource
            :rtype: ``dict``
        """
        result = {"required": [], "optional": [], "multiple": []}
        if "query_parameters" in self.config:
            for parameter in self.config["query_parameters"]:
                if ("required" in parameter) and (parameter["required"] is True):
                    result["required"].append(parameter["name"])
                else:
                    result["optional"].append(parameter["name"])
                if ("multiple" in parameter) and (parameter["multiple"] is True):
                    result["multiple"].append(parameter["name"])
        return result

    # ---------------------------------------------------------------------------------------------
    @property
    @contract
    def _query_parameter_groups(self):
        """ Lists the different groups of query parameters for the specified
            REST API resource. When query parameters are in a group, only one of
            them can be used in a query at a time, unless the 'multiple' property
            has been used for every query parameter of that group.

            :return: A dictionary of the different groups (key) of query parameters (value, is list) for the specified REST API resource
            :rtype: ``dict``
        """

        result = {}
        if "query_parameters" in self.config:
            for parameter in self.config["query_parameters"]:
                # TODO: check if string, maybe also support int?
                if ("group" in parameter) and (parameter["group"].strip() != ""):
                    if parameter["group"] not in result:
                        result[parameter["group"]] = []
                    result[parameter["group"]].append(parameter["name"])
        return result

    # ---------------------------------------------------------------------------------------------
    @property
    @contract
    def _path_parameters(self):
        """ Lists the (always required) path parameters for the specified REST API resource

            #:param resource: A string that represents the REST API resource
            #:type resource: ``string_type``

            :return: A list of the (always required) path parameters for the specified REST API resource
            :rtype: ``list(string_type)``
        """

        path_parameters = []
        if "path" in self.config:
            for part in self.config["path"]:
                if part.startswith("{") and part.endswith("}"):
                    path_parameters.append(part[1:-1])
        return path_parameters
    

class RestResource():
    '''
    A resource is defined as a single REST endpoint.
    This class wraps functionality of creating and querying this resources, starting with a
    configuration string
    '''
    
    def __init__(self, client, name, config):
        self.client = client
        self.name = name

        assert isinstance(config, ResourceParameters)
        self.config = config
        self.path = self.config.path
        self.method = self.config.method
    
    # ---------------------------------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        # catch accidential positional arguments
        
        self.validate_request(*args, **kwargs)
        return self._get()
    

    # ---------------------------------------------------------------------------------------------
    @property
    @contract
    def parameters(self):
        '''
        return the configuration parameters for this rest resource
        :return: A dictionary of the 'optional', 'required' and 'multiple' (keys) query parameters (value, a list)
        :rtype: ``dict``
        
        '''
        return self.config.as_dict
        

    #---------------------------------------------------------------------------------------------
    def validate_request(self, *args, **kwargs):
        '''
        check the input request parameters before sending it to the remote service
        '''
        
        rp = self.config
        
        #----------------------------------
        # deny superfluous input
        if args:
            raise SyntaxError("all parameters must by keyword arguments")
        
        diff = set(kwargs.keys()).difference(rp.all_parameters)
        if len(diff) > 0:
            raise SyntaxError("parameters {difference} are supplied but not usable for resource '{resource}'".format(
                difference=list(diff),
                resource=self.name
            ))

        #----------------------------------
        # Resolve path parameters in path
        resolved_path = "/".join(self.path)
        for parameter in rp.required_parameters:
            if parameter not in kwargs.keys():
                raise SyntaxError("parameter '{parameter}' is missing for resource '{resource}'".format(
                    parameter=parameter,
                    resource=self.name
                ))
        
        # construct the URL path
        path_para = {parameter: quote(kwargs[parameter], safe='') for parameter in kwargs if parameter in rp.path_parameters}
        resolved_path = resolved_path.format(**path_para)

        # Construct URL using base URL and path
        url = "{url}/{path}".format(url=self.client.url, path=resolved_path)

        # Check if valid URL
        # Only allow http or https schemes for the REST API base URL
        url_validator = URLValidator(schemes=["http", "https"])
        url_validator(url)

        #----------------------------------
        # Prepare & check query parameters
        query_parameters = {}
        intersection = set(rp.all_query_parameters).intersection(kwargs.keys())
        groups_used = {}
        for kwarg in intersection:
            for group in rp.query_parameter_groups:
                if kwarg in rp.query_parameter_groups[group]:
                    if group in groups_used:
                        raise SyntaxError(
                            "parameter '{kwarg1}' and '{kwarg2}' from group '{group}' can't be used together".format(
                                kwarg1=kwarg,
                                kwarg2=groups_used[group],
                                group=group
                            ))
                    else:
                        groups_used[group] = kwarg
                    break
            # TODO: is this necessary? wouldn't we get HTTP 400?
            if isinstance(kwargs[kwarg], list) and kwarg not in rp.multiple_parameters:
                raise SyntaxError("parameter '{kwarg}' is not multiple".format(
                    kwarg=kwarg
                ))
            else:
                query_parameters[kwarg] = kwargs[kwarg]
        
        #----------------------------------
        # depending on request type, return parameters in request or body
        if self.method == 'GET':
            request_parameters = query_parameters
            body_parameters = {}
        else:
            request_parameters = {}
            body_parameters = query_parameters
        
        self.cleaned_data = {'url': url,
                             'parameters': request_parameters,
                             'data': body_parameters,
                             }
        

    # ---------------------------------------------------------------------------------------------
    def _get(self):
        """ This function builds and sends a request for a specified REST API resource.
            The parameters are validated dynamically, depending on the configuration of said REST API resource.
            It returns a dictionary of the response or throws an appropriate error, depending on the HTTP return code.
        """

        # url and parameters
        if not 'cleaned_data' in dir(self):
            raise KeyError('request data is not cleaned. Run validate_request first')

        # Do HTTP request to REST API
        try:
            response = requests.request(method=self.method,
                                        auth=self.client.auth,
                                        verify=self.client.verifySSL,
                                        url=self.cleaned_data['url'], 
                                        params=self.cleaned_data['parameters'],
                                        json=self.cleaned_data['data'],
                                        #data=...,
                                        headers=self.config.headers
                                        )
            assert isinstance(response, requests.Response)
            
            if response.status_code > 399:
                '''
                Nicely catch exceptions 
                '''
                x = 1
                raise BCSRestResourceHTTPError(response_object=response)
            # for completeness sake: let requests check for valid output
            # code should not get here...
            response.raise_for_status()
        except ValueError as e:
            # Weird response errors: just give back the raw data. This has the risk of dismissing
            # valid errors!
            return response.content
        except requests.HTTPError as http:
            # This is a back-catcher for HTTP errors that were not caught before. Code shoul
            # not get here
            raise http
        else:
            return RestResponse(response=response, options=self.config.json_options)
            

