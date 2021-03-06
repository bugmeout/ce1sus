# -*- coding: utf-8 -*-

"""
(Description)

Created on Jan 30, 2014
"""
from ce1sus.db.classes.common import TLP


__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'


def is_user_priviledged(user):
  if user:
    return user.permissions.privileged
  return False


def is_event_viewable_group(event, group):
  if group.identifier == event.owner_group_id:
    return True
  else:
    tlp_lvl = get_max_tlp(group)
    if event.tlp_level_id >= tlp_lvl:
      return True
    else:
      grp_ids = list()
      for group in group.children:
        grp_ids.append(group.identifier)
      grp_ids.append(group.identifier)

      for eventgroup in event.groups:
        group = eventgroup.group
        if group.identifier in grp_ids:
          return True
      return False


def is_event_viewable_user(event, user):
  if is_event_owner(event, user):
    return True
  else:
    if user:
      if user.group:
        return is_event_viewable_group(event, user.group)
      else:
        return False
    else:
      return False


def is_object_viewable(instance, event_permissions, user, cache=None):
  if instance.__class__.__name__ == 'ObservableComposition':
    # always visible as the composed observable does not have a tlp level
    return True
  elif instance.properties.is_validated and instance.properties.is_shareable:
    # free for all
    return True
  elif event_permissions:
    # check if user can validate the object
    if not instance.properties.is_validated and event_permissions.can_validate:
      return True

  if user and user.group:
    user_group = user.group
    if user_group.identifier in [instance.owner_group_id, instance.creator_group_id, instance.originating_group_id]:
      # check if the user owns submitted or created the object then return True
      return True
    else:
      # check if tlp matches
      user_tlp = get_max_tlp(user_group)
      if instance.tlp_level_id >= user_tlp:
        return True

  return False


def is_event_owner(event, user):
  """
  Returns true if the event is created by the user

  :param event:
  :type event: Event
  :param user:
  :type user: User

  :returns: Boolean
  """
  if event and user:
    if is_user_priviledged(user):
      return True
    else:
      if user.group_id == event.owner_group_id:
        return True
      else:
        return False
  else:
    return False


def get_view_message(result, event_id, username, permission):
  """
  Returns the message for loggin

  :param event_id: identifer of the event
  :type event_id: Integer
  :param username:
  :type username: String
  :param result:
  :type result: Boolean
  """
  if result:
    return 'User "{1}" can perform action "{2}" on event "{0}"'.format(event_id, username, permission)
  else:
    return 'User "{1}" is not allowed perform action "{2}" on event "{0}"'.format(event_id, username, permission)


def get_item_view_message(result, event_id, item_id, username, permission):
  if result:
    return 'User "{1}" can perform action "{2}" on event "{0}" for item {3}'.format(event_id, username, permission, item_id)
  else:
    return 'User "{1}" is not allowed perform action "{2}" on event "{0}" for item {3}'.format(event_id, username, permission, item_id)


def can_user_download(event, user, cache=None):
  """
  Returns true if the user can download from the event

  :param event:
  :type event: Event
  :param user:
  :type user: User

  :returns: Boolean
  """
  if user.permissions.privileged:
    return True
  if user.group:
    result = user.group.permissions.can_download
    return result
  else:
    return False


def get_max_tlp(user_group):
  if user_group:
    if user_group.permissions.propagate_tlp:
      max_tlp = user_group.tlp_lvl
      for group in user_group.children:
        if group.tlp_lvl < max_tlp:
          max_tlp = group.tlp_lvl
        # check for group children
        child_max = get_max_tlp(group)
        if child_max < max_tlp:
          max_tlp = child_max
      return max_tlp
    else:
      return user_group.tlp_lvl
  else:
    return TLP.get_by_value('White')
