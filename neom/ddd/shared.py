# Copyright 2022 neomadas-dev
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   1. Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#   3. Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""This module is under construction.
It's used to mark the domain role for classes and models defined in the domain.
"""

from abc import ABC, ABCMeta, abstractmethod
from types import CodeType, FunctionType
from typing import (Generic, NoReturn, Type, TypeVar, _GenericAlias, cast,
                    get_type_hints)


class Stuff(ABC):
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)


class MetaEntity(ABCMeta):
  def __init__(cls, cname, bases, namespace):
    if '__annotations__' in namespace:
      initlines = ['def __init__(self']
      initbody = []
      slots = []
      idname = None
      for name, kind in get_type_hints(cls).items():
        if isinstance(kind, _GenericAlias):
          kind = cast(_GenericAlias, kind).__origin__
        initlines.append(f', {name}: {kind.__name__}')
        initbody.append(f'\n  self.{name} = {name}')
        slots.append(name)
        if isinstance(kind, IdentityAlias):
          idname = name
      initlines.append('):\n  """Entity init"""')
      initlines.extend(initbody)
      initlines.append('\n  self.Validate()')
      initcode = compile(''.join(initlines), '<ddd.shared>', 'exec')
      initfunc = FunctionType(
        InitCodeType(
          initcode.co_consts[1]),
        globals(),
        '__init__',
        None,
        cls.__init__.__closure__)
      super().__init__(cname, bases, namespace)
      cls.__init__ = initfunc
      cls.__slots__ = tuple(slots)
      if idname:
        identity = FunctionType(
          compile(f'def identity(self) -> ID: return self.{idname}',
            '<ddd.shared>', 'exec').co_consts[1], globals())
      else:
        def identity(self) -> NoReturn: raise NoIdentityError(cls)
      cls.identity = identity

  def __repr__(cls):
    items = cls.__annotations__.items()
    props = ('{}={!r}'.format(name, prop) for name, prop in items)
    return '{}<{}>'.format(cls.__name__, ', '.join(props))


def InitCodeType(c):
  return CodeType(c.co_argcount, c.co_posonlyargcount,
                  c.co_kwonlyargcount, c.co_nlocals,
                  c.co_stacksize, c.co_flags, c.co_code, c.co_consts, c.co_names,
                  c.co_varnames, c.co_filename, c.co_name, c.co_firstlineno,
                  c.co_lnotab, c.co_freevars + ('__class__',), c.co_cellvars)


T = TypeVar('T')
ID = TypeVar('ID')


class Entity(Generic[T, ID], metaclass=MetaEntity):
  """TODO: Domain model entity."""

  def __init__(self):
    super().__init__()

  def Validate(self):
    """Execute domain member validations."""

  def identity(self) -> ID:
    return NotImplemented

  def SameIdentityAs(other: T) -> bool:
    return NotImplemented


class ValueObject(Stuff):
  """TODO: Domain model value object."""


class Identity:
  """TODO: Domain model annotation for identity."""

  def __class_getitem__(cls, member: Type[object]):
    return IdentityAlias(member)


class IdentityAlias:

  __slots__ = ('_kind', '__name__')

  def __init__(self, kind: Type[object]):
    self._kind = kind
    self.__name__ = kind.__name__

  def __instancecheck__(self, obj): return self.__subclasscheck__(type(obj))

  def __subclasscheck__(self, cls): return cls == self._kind

  def __mro_entries__(self, bases): raise TypeError(
    f'Cannot subclass {self!r}')

  def __repr__(self): return f'{self._kind}'

  def __reduce__(self):
    return self._name

  def __call__(self, *args, **kwds):
    raise TypeError(f'Cannot instantiate {self!r}')

  def __instancecheck__(self, obj): raise TypeError('Cannot instance check')

  def __subclasscheck__(self, cls): raise TypeError('Cannot subclass check')


class Service(Stuff):
  """TODO: Domain service declaration."""


class Repository(Stuff):
  """TODO: Domain model entity repository."""


class Action:
  """TODO: Domain model action service."""

  @abstractmethod
  def Apply(self):
    raise NotImplementedError


class QuerySet:
  """TODO: Domain model query set application."""


class Error(Exception):
  """DDD Errors"""


class DomainError(Error):
  """Entities, repositories and services base error for user cases.
  This exceptions does not break the workflow."""


class NoIdentityError(DomainError):
  """Notify the use"""

  def __init__(self, cls):
    self._cls = cls

  def __str__(self): return f'{self._cls.__qualname__} without identity'


class RepositoryError(DomainError):
  """Find, Store, Delete, Remove errors"""


class ServiceError(DomainError):
  pass


class NotFoundError(RepositoryError):
  """Raised when Repository.Find doest not foun.
  Connection and transaction errors not included.
  """
