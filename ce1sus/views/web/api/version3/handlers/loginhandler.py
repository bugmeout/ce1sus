# -*- coding: utf-8 -*-

"""
(Description)

Created on Oct 29, 2014
"""

import cherrypy
from datetime import datetime
import math
import string

from ce1sus.controllers.admin.user import UserController
from ce1sus.controllers.base import ControllerException, ControllerNothingFoundException
from ce1sus.controllers.login import LoginController
from ce1sus.helpers.common.validator.valuevalidator import ValueValidator
from ce1sus.views.web.api.version3.handlers.restbase import RestBaseHandler, rest_method, methods, require, RestHandlerException


__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013-2014, GOVCERT Luxembourg'
__license__ = 'GPL v3+'


class LoginHandler(RestBaseHandler):

  def __init__(self, config):
    RestBaseHandler.__init__(self, config)
    self.login_controller = self.controller_factory(LoginController)
    self.user_controller = self.controller_factory(UserController)

  @rest_method(default=True)
  @methods(allowed=['POST'])
  def login(self, **args):
    try:
      credentials = args.get('json', None)
      user = None
      if credentials:
        usr = credentials.get('usr', None)
        pwd = credentials.get('pwd', None)
        if usr and pwd:
                    # check if input is valid:
          printable_chars = string.printable[:-5]
          regex = '[{0}]'.format(printable_chars) + '{1,64}'
          if (not ValueValidator.validateRegex(usr, regex, 'errorMsg')
             and
             not ValueValidator.validateRegex(pwd, regex, 'errorMsg')):
            raise ControllerException(u'Illegal input')
          self.logger.debug('A login attempt via username and password')
          user = self.login_controller.get_user_by_usr_pwd(usr, pwd)
      else:
        headers = args.get('headers', None)
        if headers:
          key = headers.get('Key', None)
          if key:
            self.logger.debug('A login attempt via api key')
            user = self.login_controller.get_user_by_apikey(key)
          else:
            raise cherrypy.HTTPError(status=401, message='No credentials given.')
        else:
          raise cherrypy.HTTPError(status=401, message='No credentials given.')
      if user:
        self.login_controller.update_last_login(user)
        # put in session
        self.put_user_to_session(user)
        self.logger.info('User "{0}" logged in'.format(user.username))
        return user.to_dict(False, False)
      else:
        self.logger.info('A login attempt was made by the disabled user {0}'.format(usr))
        raise cherrypy.HTTPError(status=401, message='User or password are incorrect.')
    except ControllerException as error:
      self.logger.info(error)
      raise cherrypy.HTTPError(status=401, message='Credentials are incorrect.')

  @rest_method()
  @methods(allowed=['GET'])
  def activation(self, **args):
    try:
      path = args.get('path')
      if len(path) > 0:
        act_str = path.pop(0)
        user = self.user_controller.get_user_by_activation_str(act_str)
        if user.is_activated:
          return {'activated': False, 'errors': 'User is already activated'}
        now = datetime.now()
        time_diff = now - user.activation_sent
        if math.floor((time_diff.seconds) / 3600) >= 24:
          return {'activated': False, 'errors': 'Activation link expired'}
        if user.permissions.disabled:
          return {'activated': False, 'errors': 'Activation link is disabled'}
        self.user_controller.activate_user(user, False)
        return{'activated': True, 'errors': None}
      else:
        raise RestHandlerException('No uuid given')
    except ControllerNothingFoundException as error:
      return {'activated': False, 'errors': 'Activation link cannot be found'}
    except ControllerException as error:
      raise RestHandlerException(error)


class LogoutHandler(RestBaseHandler):

  @rest_method(default=True)
  @methods(allowed=['GET'])
  @require()
  def logout(self, **args):
    self._destroy_session()
    return 'User logged out'
