from framework.web.controllers.base import BaseController
import cherrypy
from ce1sus.brokers.definitionbroker import ObjectDefinitionBroker, \
ObjectDefinition
from ce1sus.web.helpers.protection import require, privileged
from framework.db.broker import OperationException, BrokerException, \
  ValidationException
import types as types


class ObjectController(BaseController):


  def __init__(self):
    BaseController.__init__(self)
    self.objectBroker = self.brokerFactory(ObjectDefinitionBroker)


  @require(privileged())
  @cherrypy.expose
  def index(self):
    """
    renders the object page

    :returns: generated HTML
    """

    template = self.getTemplate('/admin/objects/objectBase.html')
    return template.render()

  @cherrypy.expose
  def leftContent(self):

    template = self.getTemplate('/admin/objects/objectLeft.html')

    objects = self.objectBroker.getAll()
    return template.render(objects=objects)

  @cherrypy.expose
  def rightContent(self, objectid=0, obj=None):
    template = self.getTemplate('/admin/objects/objectRight.html')

    if obj is None:
      if objectid is None or objectid == 0:
        obj = None
      else:
        obj = self.objectBroker.getByID(objectid)
    else:
      obj = obj

    remainingAttributes = None
    attributes = None
    if not obj is None:
      remainingAttributes = self.objectBroker.getAttributesByObject(
                                                obj.identifier, False)
      attributes = obj.attributes
    return template.render(objectDetails=obj,
                           remainingAttributes=remainingAttributes,
                           objectAttributes=attributes)


  @cherrypy.expose
  def addObject(self):
    template = self.getTemplate('/admin/objects/objectModal.html')
    return template.render(object=None, errorMsg=None)


  @require(privileged())
  @cherrypy.expose
  def modifyObject(self, identifier=None, name=None, shareTLP=0,
                  description=None, action='insert'):
    """
    modifies or inserts a object with the data of the post

    :param identifier: The identifier of the object,
                       is only used in case the action is edit or remove
    :type identifier: Integer
    :param name: The name of the object
    :type name: String
    :param description: The description of this object
    :type description: String
    :param action: action which is taken (i.e. edit, insert, remove)
    :type action: String

    :returns: generated HTML
    """
    template = self.getTemplate('/admin/objects/objectModal.html')


    obj = ObjectDefinition()
    if not action == 'insert':
      obj.identifier = identifier
    if not action == 'remove':
      obj.name = name
      obj.description = description
      try:
        if action == 'insert':
          self.objectBroker.insert(obj)
        if action == 'update':
          self.objectBroker.update(obj)
        action = None
      except ValidationException:
        self.getLogger().info('Object is invalid')
      except BrokerException as e:
        self.getLogger().info('An unexpected error occurred: {0}'.format(e))
        errorMsg = 'An unexpected error occurred: {0}'.format(e)
        action = None
        obj = None
    else:
      try:
        self.objectBroker.removeByID(obj.identifier)
        obj = None
      except OperationException:
        errorMsg = 'Cannot delete this object. The object is still referenced.'


    if action == None:
      # ok everything went right
      return self.returnAjaxOK()
    else:
      return template.render(objectDetails=obj, errorMsg=errorMsg)


  @cherrypy.expose
  def editObject(self, objectid):
    template = self.getTemplate('/admin/objects/objectModal.html')

    errorMsg = None
    try:
      obj = self.objectBroker.getByID(objectid)
    except BrokerException as e:
      obj = None
      self.getLogger().error('An unexpected error occurred: {0}'.format(e))
      errorMsg = 'An unexpected error occurred: {0}'.format(e)
    return template.render(objectDetails=obj, errorMsg=errorMsg)

  @require(privileged())
  @cherrypy.expose
  def editObjectAttributes(self, objectid, operation,
                     objectAttributes=None, remainingAttributes=None):
    """
    modifies the relation between a object and its attributes

    :param objectID: The objectID of the object
    :type objectID: Integer
    :param operation: the operation used in the context (either add or remove)
    :type operation: String
    :param remainingUsers: The identifiers of the users which the object is not
                            attributed to
    :type remainingUsers: Integer array
    :param objectUsers: The identifiers of the users which the object is
                       attributed to
    :type objectUsers: Integer array

    :returns: generated HTML
    """
    try:
      if operation == 'add':
        if not (remainingAttributes is None):
          if isinstance(remainingAttributes, types.StringTypes):
            self.objectBroker.addAttributeToObject(remainingAttributes,
                                                   objectid)
          else:
            for attribute in remainingAttributes:
              self.objectBroker.addAttributeToObject(attribute, objectid, False)
            self.objectBroker.commit()
      else:
        #Note objectAttributes may be a string or an array!!!
        if not (objectAttributes is None):
          if isinstance(objectAttributes, types.StringTypes):
            self.objectBroker.removeAttributeFromObject(objectAttributes,
                                                        objectid)
          else:
            for attribute in objectAttributes:
              self.objectBroker.removeAttributeFromObject(attribute, objectid)
            self.objectBroker.commit()
      return self.returnAjaxOK()
    except BrokerException as e:
      return e