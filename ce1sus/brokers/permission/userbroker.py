# -*- coding: utf-8 -*-

"""This module provides container classes and interfaces
for inserting data into the database.

Created on Jul 4, 2013
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'

from dagr.db.broker import BrokerBase, NothingFoundException, \
ValidationException, TooManyResultsFoundException
import sqlalchemy.orm.exc
import dagr.helpers.hash as hasher
from dagr.db.broker import BrokerException
import re
from dagr.helpers.converters import ObjectConverter
from dagr.helpers.ldaphandling import LDAPHandler
import dagr.helpers.strings as strings
from ce1sus.brokers.permission.permissionclasses import User
from dagr.helpers.hash import hashSHA1
from dagr.helpers.strings import cleanPostValue
from dagr.helpers.validator.objectvalidator import ObjectValidator


class UserBroker(BrokerBase):
  """This is the interface between python an the database"""

  def insert(self, instance, commit=True, validate=True):
    """
    overrides BrokerBase.insert
    """
    errors = False
    if validate:
      errors = not instance.validate()
      if errors:
        raise ValidationException('User to be inserted is invalid')
    if validate and not errors:
      instance.password = hasher.hashSHA1(instance.password,
                                             instance.username)
    try:
      BrokerBase.insert(self, instance, commit, validate=False)
      self.doCommit(commit)
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def update(self, instance, commit=True, validate=True):
    """
    overrides BrokerBase.insert
    """

    errors = False
    if validate:
      errors = not instance.validate()
      if errors:
        raise ValidationException('User to be updated is invalid')

    if instance.password != 'EXTERNALAUTH':
    # Don't update if the password is already a hash
      if re.match('^[0-9a-f]{40}$', instance.password) is None:
        if not errors:
          instance.password = hasher.hashSHA1(instance.password,
                                               instance.username)
    try:
      BrokerBase.update(self, instance, commit, validate=False)
      self.doCommit(commit)
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def isUserPrivileged(self, username):
    """
    Checks if the user has the privileged flag set

    :returns: Boolean
    """
    user = self.getUserByUserName(username)
    if (user.privileged == 1):
      return True
    else:
      return False

  def getBrokerClass(self):
    """
    overrides BrokerBase.getBrokerClass
    """
    return User

  def getUserByUserName(self, username):
    """
    Returns the user with the following username

    :param user: The username
    :type user: Stirng

    :returns: User
    """
    try:
      user = self.session.query(User).filter(User.username == username).one()
    except sqlalchemy.orm.exc.NoResultFound:
      raise NothingFoundException('Nothing found with ID :{0}'.format(username)
                                  )
    except sqlalchemy.orm.exc.MultipleResultsFound:
      raise TooManyResultsFoundException('Too many results found for' +
                                         'ID :{0}'.format(username))
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)
    return user

  def getUserByUsernameAndPassword(self, username, password):
    """
    Returns the user with the following username and password

    Note: Password will be hashed inside this function

    :param user: The username
    :type user: Stirng
    :param password: The username
    :type password: Stirng

    :returns: User
    """
    if password == 'EXTERNALAUTH':
      passwd = password
    else:
      passwd = hasher.hashSHA1(password, username)

    try:
      user = self.session.query(User).filter(User.username == username,
                                             User.password == passwd).one()
    except sqlalchemy.orm.exc.NoResultFound:
      raise NothingFoundException('Nothing found with ID :{0}'.format(username)
                                  )
    except sqlalchemy.orm.exc.MultipleResultsFound:
      raise TooManyResultsFoundException('Too many results found for ID ' +
                                         ':{0}'.format(username))
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)
    return user

  # pylint: disable=R0913
  @staticmethod
  def buildUser(identifier=None, username=None, password=None,
                 priv=None, email=None, action='insert', disabled=None,
                 maingroup=None, apikey=None):
    """
    puts a user with the data together

    :param identifier: The identifier of the user,
                       is only used in case the action is edit or remove
    :type identifier: Integer
    :param username: The username of the user
    :type username: strings
    :param password: The password of the user
    :type password: strings
    :param email: The email of the user
    :type email: strings
    :param priv: Is the user privileged to access the administration section
    :type priv: Integer
    :param action: action which is taken (i.e. edit, insert, remove)
    :type action: strings

    :returns: generated HTML
    """
    user = User()
    if not action == 'insert':
      user.identifier = identifier
    if not action == 'remove' and action != 'insertLDAP':
      user.email = cleanPostValue(email)
      user.password = cleanPostValue(password)
      user.username = cleanPostValue(username)
    if strings.isNotNull(disabled):
      ObjectConverter.setInteger(user, 'disabled', disabled)
    if strings.isNotNull(priv):
      ObjectConverter.setInteger(user, 'privileged', priv)
    if strings.isNotNull(maingroup):
      ObjectConverter.setInteger(user, 'group_id', maingroup)
    if action == 'insertLDAP':
      user.identifier = None
      lh = LDAPHandler.getInstance()
      ldapUser = lh.getUser(identifier)
      user.username = ldapUser.uid
      user.password = ldapUser.password
      user.email = ldapUser.mail
      user.disabled = 1
      user.privileged = 0
      user.group_id = 1
    if apikey == '1':
      # generate key
      user.apiKey = hashSHA1('{0}{1}APIKey'.format(user.email, user.username))
    return user

  def getUserByApiKey(self, apiKey):
    # check if api key exists
    try:
      result = self.session.query(User).filter(
                       User.apiKey == apiKey).one()
      return result
    except sqlalchemy.orm.exc.NoResultFound:
      raise NothingFoundException('Nothing found with apikey :{0}'.format(
                                                                  apiKey))
    except sqlalchemy.orm.exc.MultipleResultsFound:
      raise TooManyResultsFoundException(
                    'Too many results found for apikey :{0}'.format(apiKey))
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      raise BrokerException(e)

  def getAll(self):
    """
    Returns all getBrokerClass() instances

    Note: raises a NothingFoundException or a TooManyResultsFound Exception

    :returns: list of instances
    """
    try:
      result = self.session.query(self.getBrokerClass()
                                  ).order_by(User.username.asc()).all()
    except sqlalchemy.orm.exc.NoResultFound:
      raise NothingFoundException('Nothing found')
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      raise BrokerException(e)

    return result
