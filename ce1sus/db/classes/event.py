# -*- coding: utf-8 -*-

"""
(Description)

Created on Oct 16, 2014
"""
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, Table, ForeignKey
from sqlalchemy.types import Unicode, Integer, Text, Boolean, BIGINT

from ce1sus.db.classes.base import ExtendedLogingInformations
from ce1sus.db.classes.common import Status, Risk, Analysis, TLP, Properties
from ce1sus.db.classes.permissions import Group, Association
from ce1sus.db.common.broker import DateTime
from ce1sus.db.common.session import Base
from ce1sus.helpers.bitdecoder import BitBase


__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013-2014, GOVCERT Luxembourg'
__license__ = 'GPL v3+'


_REL_EVENT_ASSOCIATIONS = Table('event_has_associations', getattr(Base, 'metadata'),
                                Column('ehg_id', BIGINT, primary_key=True, nullable=False, index=True),
                                Column('event_id', BIGINT, ForeignKey('events.event_id'), nullable=False, index=True),
                                Column('association_id', BIGINT, ForeignKey('associations.association_id'), nullable=False, index=True)
                                )

_REL_EVENT_GROUPS = Table('event_has_groups', getattr(Base, 'metadata'),
                          Column('ehg_id', BIGINT, primary_key=True, nullable=False, index=True),
                          Column('group_id', BIGINT, ForeignKey('groups.group_id'), nullable=False, index=True),
                          Column('event_id', BIGINT, ForeignKey('events.event_id'), nullable=False, index=True)
                          )


class Event(ExtendedLogingInformations, Base):

  title = Column('title', Unicode(45), index=True, unique=True, nullable=False)
  description = Column('description', Text)
  tlp_level_id = Column('tlp_level_id', Boolean, default=3, nullable=False)
  status_id = Column('status_id', Boolean, default=0, nullable=False)
  risk_id = Column('risk_id', Boolean, nullable=False, default=0)
  analysis_id = Column('analysis_id', Boolean, nullable=False, default=0)
  comments = relationship('Comment')

  # TODO: Add administration of minimal objects -> checked before publishing
  required_objects = relationship('ObjectDefinition')

  associations = relationship(Association,
                              secondary='event_has_associations',
                              backref='events')
  groups = relationship(Group,
                        secondary='event_has_groups',
                        backref='events')
  objects = relationship('Object',
                         primaryjoin='and_(event.identifier==object.event_id, object.parent_object_id==None)')
  __tlp_obj = None
  dbcode = Column('code', Integer)
  __bit_code = None
  last_publish_date = Column('last_publish_date', DateTime)

  @property
  def properties(self):
    """
    Property for the bit_value
    """
    if self.__bit_code is None:
      if self.dbcode is None:
        self.__bit_code = Properties('0', self)
      else:
        self.__bit_code = Properties(self.dbcode, self)
    return self.__bit_code

  @properties.setter
  def properties(self, bitvalue):
    """
    Property for the bit_value
    """
    self.__bit_code = bitvalue
    self.dbcode = bitvalue.bit_code

  @property
  def status(self):
    """
    returns the status

    :returns: String
    """
    return Status.get_by_id(self.status_id)

  @status.setter
  def set_status(self, status_text):
    """
    returns the status

    :returns: String
    """
    self.status_id = Status.get_by_value(status_text)

  @property
  def risk(self):
    """
    returns the status

    :returns: String
    """
    return Risk.get_by_id(self.risk_id)

  @risk.setter
  def risk(self, risk_text):
    """
    returns the status

    :returns: String
    """
    self.risk_id = Risk.get_by_value(risk_text)

  @property
  def analysis(self):
    """
    returns the status

    :returns: String
    """
    return Analysis.get_by_id(self.analysis_status_id)

  @analysis.setter
  def analysis(self, text):
    """
    returns the status

    :returns: String
    """
    self.analysis_status_id = Analysis.get_by_value(text)

  @property
  def tlp(self):
    """
      returns the tlp level

      :returns: String
    """
    if self.__tlp_obj is None:
      self.__tlp_obj = TLP(self.tlp_level_id)
    return self.__tlp_obj

  @tlp.setter
  def tlp(self, text):
    """
    returns the status

    :returns: String
    """
    self.__tlp_obj = None
    self.analysis_status_id = TLP.get_by_value(text)
