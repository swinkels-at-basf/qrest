'''
This module handle authentication against a variety of REST services
'''


import os
import logging
from typing import Optional
from netrc import netrc
from urllib.parse import urlparse
import requests


# ================================================================================================
# local imports
from ..exception import RestLoginError

logger = logging.getLogger(__name__)

# ==========================================================================================
class RESTAuthentication(requests.auth.HTTPBasicAuth):
    '''
    Standard authentication methods and credentials
    This basic authentication does not complain if user is not logging in
    explicitely. This is the most silent form of authentication
    '''

    is_logged_in = False
    username = None
    password = None

    def __init__(self, rest_client, auth_config_object=None):
        """
        basic auth that uses user/pass or netrc
        this is a subclass of HTTPBasicAuth, but differs in that it requires a specific call to
        login() to allow netrc and embedding.

        :param rest_client: A reference to the RESTclient object
        :type rest_client: ``RESTclient``

        """

        self.rest_client = rest_client
        self.auth_config_object = auth_config_object

    @property
    def login_tuple(self):
        '''
        returns a username/password tuple to use in basic authentication
        '''
        return (self.username, self.password)

    @staticmethod
    def is_valid_credential(credential):
        """ Determines whether the given credential is valid.
            The credential should not be None and should not be the empty string.

            :param credential: The credential to check
            :type credential: ``string_type_or_none``
        """
        return credential is not None and credential.strip() != ""

    def are_valid_credentials(self, username, password):
        """ Determines whether given credentials are valid.
            Both username and password should not be None and should not be the empty string.

            :param username: The username to check
            :type username: ``string_type_or_none``

            :param password: The password to check
            :type password: ``string_type_or_none``
        """

        if self.is_valid_credential(username):
            return True
        else:
            if self.is_valid_credential(password):
                raise RestLoginError('provided password but not a username')
            else:
                return False

    # -------------------------------------------------------------------------------
    def login(self):
        '''
        placeholder to enforce subclasses to customize the login method
        '''
        raise NotImplementedError('Define login procedure in subclass')


# ==========================================================================================
class UserPassAuth(RESTAuthentication):
    '''
    Authentication that enforces username / password
    '''

    is_logged_in = False

    # -------------------------------------------------------------------------------
    def login(self, username=None, password=None):
        """ Explicitly do a login with supplied username and password.
            If username and password are supplied, it will use those to login.
            If either or both username and/or password is missing, will try to retrieve the credentials from the netrc file.

            :param username: The user for authenticating with the CAS end-point
            :type username: ``string_type_or_none``

            :param password: The password for authenticating with the CAS end-point
            :type password: ``string_type_or_none``
        """

        if not self.are_valid_credentials(username, password):
            raise ValueError("No or empty username and/or password supplied")
        else:
            self.username = username
            self.password = password

        self.is_logged_in = True


# ==========================================================================================
class NetRCAuth(RESTAuthentication):
    '''
    Authentication that enforces username / password
    '''

    netrc_path = os.path.expanduser("~/.netrc")
    is_logged_in = False

    # -------------------------------------------------------------------------------
    #def __init__(self, rest_client, config):
        #super(UserPassAuth, self).__init__(rest_client)


    # -------------------------------------------------------------------------------
    def login(self, netrc_path: Optional[str] = os.path.expanduser("~/.netrc")):
        """ Explicitly do a login with supplied username and password.
            If username and password are supplied, it will use those to login.
            If either or both username and/or password is missing, will try to retrieve the credentials from the netrc file.

            :param netrc_path: The network path to the netrc file
        """

        if netrc_path:
            logger.debug("Retrieving using netrc.")
            try:
                self.netrc_path = os.path.expanduser(netrc_path)
            except AttributeError as e:
                raise ValueError('could not expand netrc-path. error is "%s"' % str(e))
            nrc = netrc(file=self.netrc_path)
            host = urlparse(self.rest_client.url).hostname
            try:
                (netrc_login, _, netrc_password) = nrc.authenticators(host)
            except TypeError:
                raise ValueError("No credentials found for host '{host}' or 'default' in the netrc file at location '{location}'".format(host=host, location=self.netrc_path))
            if self.are_valid_credentials(netrc_login, netrc_password):
                self.username = netrc_login
                self.password = netrc_password
            else:
                raise ValueError("No valid credentials found for host '{host}' or 'default' in the netrc file at location '{location}'".format(host=host, location=self.netrc_path))
        else:
            raise ValueError("No Netrc path supplied")


# ==========================================================================================
class UserPassOrNetRCAuth(RESTAuthentication):
    '''
    wrapper to allow both netRC and User+Pass logins
    '''

    def login(self, netrc_path: Optional[str] = os.path.expanduser("~/.netrc"), username: Optional[str] = None, password: Optional[str] = None):
        """
        Allow logins via either netRC or user/pass.
        If netrc is true, try this. Else, try user/pass if supplied.
        If neither is available, raise error

        :param netrc_path: The path to the Netrc file
        :param username: The user for authenticating with the CAS end-point
        :param password: The password for authenticating with the CAS end-point
        """

        if username and password:
            parent_auth = UserPassAuth(rest_client=self.rest_client)
            parent_auth.login(username=username, password=password)
        elif netrc_path:
            parent_auth = NetRCAuth(rest_client=self.rest_client, auth_config_object=self.auth_config_object)
            parent_auth.login(netrc_path=netrc_path)
        else:
            raise RestLoginError('not enough data is provided to login')
        self.username = parent_auth.username
        self.password = parent_auth.password

        self.is_logged_in = True




# ==========================================================================================
class AuthConfig(object):
    '''
    Configuration and validation for custom authentication schemas
    '''
    pass


# ==========================================================================================
class UserPassAuthConfig(AuthConfig):
    '''
    Allow authentication via NetRC or User/Password
    '''

    authentication_module = UserPassAuth


# ==========================================================================================
class NetrcOrUserPassAuthConfig(AuthConfig):
    '''
    Allow authentication via NetRC or User/Password
    '''

    authentication_module = UserPassOrNetRCAuth


