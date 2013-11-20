# -*- coding: utf-8 -*-

"""This module provides container classes and interfaces
for inserting data into the database.

Created on Jul 9, 2013
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'

from dagr.db.broker import BrokerBase, ValidationException, \
NothingFoundException, TooManyResultsFoundException, \
BrokerException
import sqlalchemy.orm.exc
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from dagr.db.session import BASE, SessionManager
from sqlalchemy.types import DateTime
from ce1sus.brokers.permission.permissionclasses import User
from dagr.helpers.validator.objectvalidator import ObjectValidator
from ce1sus.brokers.definition.definitionclasses import AttributeDefinition
from ce1sus.brokers.definition.attributedefinitionbroker import \
                                              AttributeDefinitionBroker
from ce1sus.brokers.valuebroker import ValueBroker
from ce1sus.web.helpers.handlers.base import HandlerBase
from ce1sus.brokers.event.eventclasses import ObjectAttributeRelation
from dagr.db.broker import IntegrityException
from ce1sus.api.restclasses import RestAttribute
from ce1sus.helpers.bitdecoder import BitValue


class Attribute(BASE):
  """This is a container class for the ATTRIBUTES table."""

  def __init__(self):
    pass

  __tablename__ = "Attributes"
  identifier = Column('attribute_id', Integer, primary_key=True)
  def_attribute_id = Column(Integer,
                            ForeignKey('DEF_Attributes.def_attribute_id'))
  definition = relationship(AttributeDefinition,
              primaryjoin='AttributeDefinition.identifier==' +
              'Attribute.def_attribute_id', innerjoin=True)
  object_id = Column(Integer, ForeignKey('Objects.object_id'))
  object = relationship("Object",
                        primaryjoin='Object.identifier==Attribute.object_id')
  created = Column('created', DateTime)
  modified = Column('modified', DateTime)
  creator_id = Column('creator_id', Integer,
                            ForeignKey('Users.user_id'))
  creator = relationship(User,
                         primaryjoin="Attribute.creator_id==User.identifier")
  modifier_id = Column('modifier_id', Integer,
                            ForeignKey('Users.user_id'))
  modifier = relationship(User,
                          primaryjoin="Attribute.modifier_id==User.identifier")
  ioc = Column('ioc', Integer)
  __value_id = None
  __value = None
  __valueObject = None
  dbcode = Column('code', Integer)
  __bitCode = None

  @property
  def bitValue(self):
    if self.__bitCode is None:
        self.__bitCode = BitValue(self.dbcode, self)
    return self.__bitCode

  @bitValue.setter
  def bitValue(self, bitvalue):
    self.__bitCode = bitvalue

  @property
  def value_id(self):
    if self.__value_id is None:
      if self.__value is None:
        valueBroker = SessionManager.getInstance().brokerFactory(ValueBroker)
        self.__value = valueBroker.getByAttribute(self)
      else:
        self.__value_id = self.__value.identifier

    return self.__value_id

  @value_id.setter
  def value_id(self, value):
    self.__value_id = value

  @property
  def key(self):
    """
    returns the name of the definition

    :returns: String
    """
    return getattr(self.definition, 'name')

  @property
  def value(self):
    """
    returns the actual value of the attribute

    :returns: Any
    """
    if self.__valueObject is None and self.__value is None:
      # try to get the value some how...
      try:
        attributeBroker = SessionManager.getInstance().brokerFactory(
                                                                AttributeBroker
                                                                    )
        attributeBroker.getSetValues(self)
        return self.__value
      except BrokerException:
        return self.__value
    else:
      return self.__value

  @value.setter
  def value(self, value):
    """
    setter for the attribute value

    :param value: value to set
    :type value: Any
    """
    self.__value = value

  @property
  def isIOC(self):
    if self.ioc == 1:
      return 'Yes'
    else:
      return 'No'

  def validate(self):
    """
    Checks if the attributes of the class are valid

    :returns: Boolean
    """
    ObjectValidator.validateDigits(self, 'def_attribute_id')
    ObjectValidator.validateDigits(self, 'object_id')
    ObjectValidator.validateDigits(self, 'creator_id')
    ObjectValidator.validateDigits(self, 'modifier_id')
    ObjectValidator.validateDateTime(self, 'created')
    ObjectValidator.validateDateTime(self, 'modified')
    return ObjectValidator.isObjectValid(self)

  def toRestObject(self):
    result = RestAttribute()
    result.definition = self.definition.toRestObject()
    result.value = self.value
    result.ioc = self.ioc

    return result


class AttributeBroker(BrokerBase):
  """
  This broker handles all operations on attribute objects
  """
  def __init__(self, session):
    BrokerBase.__init__(self, session)
    self.valueBroker = ValueBroker(session)
    self.attributeDefinitionBroker = AttributeDefinitionBroker(session)

  def getBrokerClass(self):
    """
    overrides BrokerBase.getBrokerClass
    """
    return Attribute

  def getSetValues(self, attribute):
    """sets the real values for the given attribute"""
    # execute select for the values
    try:
      value = self.valueBroker.getByAttribute(attribute)
      # value is an object i.e. StringValue and the value of the attribute is
      # the value of the value object
      # get handler
      handler = HandlerBase.getHandler(attribute.definition)
      # convert the attribute with the helper to a single line value
      attribute.value = handler.convertToAttributeValue(value)
      attribute.value_id = value.identifier
    except sqlalchemy.orm.exc.NoResultFound:
      raise NothingFoundException('No value found for attribute :{0}'.format(
                                                  attribute.definition.name))
    except sqlalchemy.orm.exc.MultipleResultsFound:
      raise TooManyResultsFoundException(
            'Too many results found for attribute :{0}'.format(
                                    attribute.definition.name))
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def createRelations(self, instance, commit=False):
    clazz = self.valueBroker.getClassByAttribute(instance)
    # find the same values!
    sameSalues = self.valueBroker.lookforValue(clazz,
                                           instance.value)

    # add them to relation table
    for sameValue in sameSalues:
      # only consider the events which are not part of the current event and

      if ((sameValue.attribute.object.event.identifier !=
           instance.object.event.identifier)
          and (instance.definition.relation == 1)):
        # one way
        relation = ObjectAttributeRelation()
        relation.ref_object_id = instance.object.identifier
        relation.object = instance.object
        relation.attribute_id = instance.identifier
        relation.attribute = instance
        relation.sameAttribute_id = sameValue.attribute.identifier
        relation.sameAttribute = sameValue.attribute
        try:
          BrokerBase.insert(self, relation, False)
        except IntegrityException:
          self.getLogger().debug('Duplicate found')
        # the other way
        relation = ObjectAttributeRelation()
        relation.ref_object_id = sameValue.attribute.object.identifier
        relation.object = sameValue.attribute.object
        relation.attribute_id = sameValue.attribute.identifier
        relation.attribute = sameValue.attribute
        relation.sameAttribute_id = instance.identifier
        relation.sameAttribute = instance
        try:
          BrokerBase.insert(self, relation, False)
        except IntegrityException:
          self.getLogger().debug('Duplicate found')
    self.doCommit(commit)

  def insert(self, instance, commit=True, validate=True):
    """
    overrides BrokerBase.insert
    """
    # validation of the value of the attribute first
    # get the definition containing the definition how to validate an attribute
    definition = instance.definition
    ObjectValidator.validateRegex(instance,
                                  'value',
                                  definition.regex,
                                  'The value does not match {0}'.format(
                                                            definition.regex),
                                  True)
    errors = not instance.validate()
    if errors:
      raise ValidationException('Attribute to be inserted is invalid')

    try:
      # insert value for value table
      BrokerBase.insert(self, instance, False, validate)

      self.createRelations(instance)

      self.valueBroker.inserByAttribute(instance, False)
      self.doCommit(commit)
    except BrokerException as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def update(self, instance, commit=True, validate=True):
    """
    overrides BrokerBase.update
    """
    # validation of the value of the attribute first
    definition = instance.definition
    ObjectValidator.validateRegex(instance,
                                  'value',
                                  definition.regex,
                                  'The value does not match {0}'.format(
                                                          definition.regex),
                                  False)
    errors = not instance.validate()
    if errors:
      raise ValidationException('Attribute to be updated is invalid')
    try:
      BrokerBase.update(self, instance, False, validate)
      # updates the value of the value table
      self.doCommit(False)
      self.valueBroker.updateByAttribute(instance, False)
      self.doCommit(commit)
    except BrokerException as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def removeByID(self, identifier, commit=True):
    try:
      attribute = self.getByID(identifier)
      self.valueBroker.removeByAttribute(attribute, False)
        # first remove values
      self.doCommit(False)
        # remove attribute
      BrokerBase.removeByID(self,
                            identifier=attribute.identifier,
                            commit=False)
      self.doCommit(commit)
    except BrokerException as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def removeAttributeList(self, attributes, commit=True):
    """
      Removes all the attributes of the list

      :param attributes: List of attributes
      :type attributes: List of Attributes
    """
    try:
      for attribute in attributes:
        # remove attributes
        self.removeByID(attribute.identifier, False)
        self.doCommit(False)
      self.doCommit(commit)
    except BrokerException as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def __lookForValueAndAttribID(self,
                                clazz,
                                value,
                                attributeDefinitionID,
                                operand='=='):
    try:
      if operand == '==':
        return self.session.query(clazz).join(clazz.attribute).filter(
                  Attribute.def_attribute_id == attributeDefinitionID,
                  clazz.value == value
                        ).all()
      if operand == '<':
        return self.session.query(clazz).join(clazz.attribute).filter(
                  Attribute.def_attribute_id == attributeDefinitionID,
                  clazz.value < value
                        ).all()
      if operand == '>':
        return self.session.query(clazz).join(clazz.attribute).filter(
                  Attribute.def_attribute_id == attributeDefinitionID,
                  clazz.value > value
                        ).all()
      if operand == '<=':
        return self.session.query(clazz).join(clazz.attribute).filter(
                  Attribute.def_attribute_id == attributeDefinitionID,
                  clazz.value <= value
                        ).all()
      if operand == '>=':
        return self.session.query(clazz).join(clazz.attribute).filter(
                  Attribute.def_attribute_id == attributeDefinitionID,
                  clazz.value >= value
                        ).all()
      if operand == 'like':
        return self.session.query(clazz).join(clazz.attribute).filter(
                  Attribute.def_attribute_id == attributeDefinitionID,
                  clazz.value.like('%{0}%'.format(value))
                        ).all()
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def __lookForValue(self, clazz, value, operand='=='):
    try:
      if operand == '==':
        return self.session.query(clazz).filter(
                  clazz.value == value
                        ).all()
      if operand == '<':
        return self.session.query(clazz).filter(
                  clazz.value < value
                        ).all()
      if operand == '>':
        return self.session.query(clazz).filter(
                  clazz.value > value
                        ).all()
      if operand == '<=':
        return self.session.query(clazz).filter(
                  clazz.value <= value
                        ).all()
      if operand == '>=':
        return self.session.query(clazz).filter(
                  clazz.value >= value
                        ).all()
      if operand == 'like':
        return self.session.query(clazz).filter(
                  clazz.value.like('%{0}%'.format(value))
                        ).all()
    except sqlalchemy.exc.SQLAlchemyError as e:
      self.getLogger().fatal(e)
      self.session.rollback()
      raise BrokerException(e)

  def lookforAttributeValue(self, attributeDefinition, value, operand='=='):
    """
    returns a list of matching values

    :param attributeDefinition: attribute definition to use for the lookup
    :type attributeDefinition: AttributeDefinition
    :param value: Value to look for
    :type value: String

    :returns: List of clazz
    """
    result = list()
    if attributeDefinition is None:
      # take all classes into account
      tables = AttributeDefinition.getTableDefinitions(False)
      for classname in tables.iterkeys():
        clazz = ValueBroker.getClassByClassString(classname)
        try:
          needle = clazz.convert(value.strip())
          result = result + self.__lookForValue(clazz, needle, operand)
        except:
          # either it works or doesn't
          pass

    else:
      clazz = ValueBroker.getClassByAttributeDefinition(attributeDefinition)
      result = self.__lookForValueAndAttribID(clazz,
                                            value,
                                            attributeDefinition.identifier,
                                            operand)

    return result
