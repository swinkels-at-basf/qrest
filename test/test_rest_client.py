import unittest
import bcs_rest_client as client

class TestInvalidResourceError(unittest.TestCase):
    
    def test_raise(self):
        from bcs_rest_client.utils import InvalidResourceError
        
        def broken_function():
            name = 'rest client name'
            resource = 'resource_name'
            raise InvalidResourceError(name, resource)
        
        with self.assertRaises(InvalidResourceError):
            broken_function()

    def test_try(self):
        from bcs_rest_client.utils import InvalidResourceError
        
        try:
            name = 'rest client name'
            resource = 'resource_name'
            raise InvalidResourceError(name, resource)
        except InvalidResourceError as e:
            expected = '"\'resource_name\' is not a valid resource for \'rest client name\'"'
            received = str(e)
            self.assertEqual(expected, received)
            
        
            
class TestRestClient(unittest.TestCase):

    url = "https://example.com"

    def test_string_contract(self):

        contract = client.string_type
        contract.check("")
        contract.check("123")
        contract.fail(None)
        contract.fail(123)
        contract = client.string_type_or_none
        contract.check("")
        contract.check("123")
        contract.check(None)
        contract.fail(123)

    def test_init_user(self):

        rc = client.RestClient(url=self.url)
        self.assertEqual(rc.auth, None)
        rc = client.RestClient(url=self.url, user="test")
        self.assertEqual(rc.auth, ('test', ''))
        rc = client.RestClient(url=self.url, user="test", password=None)
        self.assertEqual(rc.auth, ('test', ''))
        rc = client.RestClient(url=self.url, user="test", password="pass")
        self.assertEqual(rc.auth, ('test', 'pass'))
        rc = client.RestClient(url=self.url, user=None)
        self.assertEqual(rc.auth, None)

    @unittest.expectedFailure
    def test_init_wrong_type(self):

        client.RestClient(url=self.url, user=123)

    def test_init_password(self):

        rc = client.RestClient(url=self.url)
        self.assertEqual(rc.auth, None)
        rc = client.RestClient(url=self.url, password="test")
        self.assertEqual(rc.auth, None)

    def test_init_resources(self):

        rc = client.RestClient(url=self.url)
        self.assertEqual(rc.resources, [])
        resources = {
            "some_function_name": {
                "path": ["some", "collection", "{id}"],
                "method": "GET",
                "query_parameters": [
                    {"name": "some_parameter"}, 
                    {"name": "alias", "group": "likeSearch"},
                    {"name": "markerUid", "group": "likeSearch"},
                    {"name": "breedingContactEmployeeId", "group": "exact", "required": True},
                    {"name": "researchContactEmployeeId", "group": "exact", "required": True},
                ]
            }
        }
        rc = client.RestClient(url=self.url, config=resources)
        self.assertEqual(rc.resources, ['some_function_name'])
        self.assertEqual(len(rc.resources), 1)
        self.assertEqual(len(rc.list_parameters("some_function_name")), 2)
        self.assertEqual(len(rc.list_path_parameters("some_function_name")), 1)
        self.assertEqual(len(rc.list_query_parameters("some_function_name")["optional"]), 3)
        self.assertEqual(len(rc.list_query_parameters("some_function_name")["required"]), 2)
        self.assertEqual(len(rc.list_query_parameter_groups("some_function_name")), 2)
        
        # also test direct addressing
        f = rc.some_function_name
        self.assertEqual(len(f.parameters), 2)
        self.assertEqual(len(f.config.path_parameters), 1)
        self.assertEqual(len(f.config.query_parameters["optional"]), 3)
        self.assertEqual(len(f.config.query_parameters["required"]), 2)
        self.assertEqual(len(f.config.query_parameter_groups), 2)
        self.assertEqual(len(f.config.multiple_parameters), 0)

        
    def test_init_resources_no_config(self):

        rc = client.RestClient(url=self.url)
        self.assertEqual(rc.resources, [])
        resources = {}
        rc = client.RestClient(url=self.url, config=resources)
        with self.assertRaises(Exception):
            rc.create_rest_resource('resource_name', config=resources)

    #@unittest.expectedFailure
    #def test_init_resources_wrong_syntax_path(self):

        #rc = client.RestClient(url=self.url)
        #self.assertEqual(rc.resources, [])
        #resources = {
            #"some_function_name": {
                #"path": ["some", "collection", "{id}", "{data}"],
                #"method": "GET",
                #"query_parameters": [
                    #{"name": "some_parameter"}
                #]
            #}
        #}
        #rc = client.RestClient(url=self.url, config=resources)

    #@unittest.expectedFailure
    #def test_init_resources_wrong_syntax_query(self):

        #rc = client.RestClient(url=self.url)
        #self.assertEqual(rc.resources, {})
        #resources = {
            #"some_function_name": {
                #"path": ["some", "collection", "{id}"],
                #"method": "GET",
                #"query_parameters": [
                    #{"name": "some_parameter"},
                    #{"name": "data"}
                #]
            #}
        #}
        #rc = client.RestClient(url=self.url, config=resources)

    def test_init_url(self):

        rc = client.RestClient(url=self.url)
        self.assertEqual(rc.url, self.url)

    def test_init_url_ipv4(self):

        rc = client.RestClient(url="https://192.168.1.1")
        self.assertEqual(rc.url, 'https://192.168.1.1')

    def test_init_url_ipv6(self):

        rc = client.RestClient(url="http://[2001:0db8:0a0b:12f0:0000:0000:0000:0001]")
        self.assertEqual(rc.url, 'http://[2001:0db8:0a0b:12f0:0000:0000:0000:0001]')
        rc = client.RestClient(url="http://[2001:db8:a0b:12f0::1]")
        self.assertEqual(rc.url, 'http://[2001:db8:a0b:12f0::1]')

    def test_init_url_host(self):

        rc = client.RestClient(url="http://localhost")
        self.assertEqual(rc.url, 'http://localhost')

    @unittest.expectedFailure
    def test_init_url_fail_no_scheme(self):

        client.RestClient(url="example.com")

    @unittest.expectedFailure
    def test_init_url_fail_invalid_scheme(self):

        client.RestClient(url="ftp://example.com")

    @unittest.expectedFailure
    def test_init_url_fail_invalid_ipv4(self):

        client.RestClient(url="https://255.255.1")


if __name__ == '__main__':
    unittest.main()
