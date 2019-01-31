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
"""Creates a function decorator to protect execution with a lock."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import threading

_LOCK_ATTR_NAME = '_lock'


# TODO(aarg): Add a lock implementation that lets read operation occur at the
# same time (i.e. less restrictive).
class LockedClass(object):
  """Initializes an object with a lock attribute."""

  def __init__(self):
    if hasattr(self, _LOCK_ATTR_NAME):
      raise ValueError('Object already has a `{}` attribute.')
    setattr(self, _LOCK_ATTR_NAME, threading.Lock())


def locked_method(fn):
  """Wraps a class's method so it's locked.

  Args:
    fn: Object's method with the following signature:
      * Args:
        * self: Instance of the class.
        * *args: Additional positional arguments.
        * **kwargs: Additional keyword arguments.
      Note that the instance must have a `_lock` attribute.

  Returns:
    A function with same signature as the input function.
  """
  def _decorated(self, *args, **kwargs):
    lock = getattr(self, _LOCK_ATTR_NAME, None)
    if not lock:
      raise AttributeError(
          'Object {} expected to have a `{}` attribute.'.format(
              self, _LOCK_ATTR_NAME))
    with lock:
      return fn(self, *args, **kwargs)
  return _decorated
