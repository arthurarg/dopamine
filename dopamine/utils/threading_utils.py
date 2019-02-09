# coding=utf-8
# Copyright 2018 The Dopamine Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module to decouple object attributes and make them local to threads.

The `local_attributes` class decorator defines a custom getter, setter and
deleter for each specified attribute. These getter, setter and deleter actually
wrap internal attributes that are thread specific.

Each attribute has a default value that initializes the local value the first
time they are called in a thread. To set these default values, use the
`initialize_local_attributes` helper of this module.

Example of usage:
  ```python
  @local_attributes(['attr'])
  class MyClass(object):

    def __init__(self, attr_default_value):
      initialize_local_attributes(self, attr=attr_default_value)
  ```

More precisely, for each attribute specified by the user, we create internal
attributes that have a name specific to each thread. The custom getter, setter,
and deleter access these internal attributes by providing the name of the
current thread.
To each specified attribute can also be associated a global default value that
is stored in another internal attribute and that specifies which is the
initial local value of the attribute in a new thread. This default value can be
set at the object initialization.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import threading


def _get_internal_name(name):
  """Returns the internal thread local name of an attribute.

  For each specified attribute, we create a attribute which's name depends on the
  current thread to store thread local value for that attribute. This methods
  provides the name of this thread specific attribute.

  Args:
    name: str, name of the exposed attribute.
  Returns:
    str, name of the internal attribute storing thread local value.
  """
  return '__' + name + '_' + str(threading.current_thread().ident)


def _get_default_value_name(name):
  """Returns the global default value of an attribute.

  For each specified attribute, we create a global default value that is
  object-specific and not thread-specific. This gloal deafault value is stored
  in an internal attribute that is named `_attr_default` where `attr` is the
  name of the specified attribute.

  Args:
    name: str, name of the exposed attribute.
  Returns:
    str, name of the internal attribute storing thread local value.
  """
  return '_' + name + '_default'


def _add_property(cls, attr_name):
  """Adds a property to a given class.

  The a setter, getter and deleter are added to the given class with to the
  provided attribute name.
  These methods actually apply to an intenal variable that is thread-specific.
  Hence the result of these methods depends on the local thread.

  Note that when the getter is called and the local attribute is not found the
  getter will initialize the local value to the global default value.
  See `initialize_local_attributes` for more details.

  Args:
    cls: A class to add the poperty to.
    attr_name: str, name of the property to create.
  """
  def _set(self, val):
    setattr(self, _get_internal_name(attr_name), val)

  def _get(self):
    if not hasattr(self, _get_internal_name(attr_name)):
      _set(self, getattr(self, _get_default_value_name(attr_name)))
    return getattr(self, _get_internal_name(attr_name))

  def _del(self):
    delattr(self, _get_internal_name(attr_name))

  setattr(cls, attr_name, property(_get, _set, _del))


def local_attributes(attributes):
  """Creates a decorator that add properties to the decorated class.

  Args:
    attributes: List[str], names of the wrapped attributes to add to the class.
  Returns:
    A class decorator.
  """
  def _decorator(cls):
    for attr_name in attributes:
      _add_property(cls, attr_name)
    return cls
  return _decorator


def initialize_local_attributes(obj, **kwargs):
  """Sets global default values for local attributes.

  Each attribute has a global default value and local values that are specific
  to each thread.
  In each thread, the first time the getter is called it is initialized to the
  global default value. This helper function is to set these default value.

  Args:
    obj: The object that has the local attributes.
    **kwargs: The default value for each local attribute.
  """
  for key, val in kwargs.items():
    setattr(obj, _get_default_value_name(key), val)
