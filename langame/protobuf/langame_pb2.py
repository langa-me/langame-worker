# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: langame/protobuf/langame.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='langame/protobuf/langame.proto',
  package='langame.protobuf',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x1elangame/protobuf/langame.proto\x12\x10langame.protobuf\"$\n\x05Topic\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\t\"9\n\x08Question\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\t\x12\x10\n\x08\x63ontexts\x18\x03 \x03(\t\"e\n\x03Tag\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\t\x12\r\n\x05score\x18\x03 \x01(\x01\x12\r\n\x05human\x18\x04 \x01(\x08\x12\x10\n\x08question\x18\x05 \x01(\t\x12\x11\n\tgenerated\x18\x06 \x01(\x08\"\xd9\x01\n\x04User\x12\x0b\n\x03uid\x18\x01 \x01(\t\x12\r\n\x05\x65mail\x18\x02 \x01(\t\x12\x14\n\x0c\x64isplay_name\x18\x03 \x01(\t\x12\x14\n\x0cphone_number\x18\x04 \x01(\t\x12\x11\n\tphoto_url\x18\x05 \x01(\t\x12\x0e\n\x06online\x18\x06 \x01(\x08\x12\x0e\n\x06google\x18\x07 \x01(\x08\x12\x10\n\x08\x66\x61\x63\x65\x62ook\x18\x08 \x01(\x08\x12\r\n\x05\x61pple\x18\t \x01(\x08\x12\x18\n\x10\x66\x61vourite_topics\x18\n \x03(\t\x12\x0b\n\x03tag\x18\x0b \x01(\t\x12\x0e\n\x06tokens\x18\x0c \x03(\t\"F\n\x0fUserPreferences\x12\x0b\n\x03uid\x18\x01 \x01(\t\x12&\n\x1eunknown_people_recommendations\x18\x02 \x01(\x08*=\n\x10InteractionLevel\x12\x07\n\x03\x42\x41\x44\x10\x00\x12\x0b\n\x07\x41VERAGE\x10\x01\x12\t\n\x05GREAT\x10\x02\x12\x08\n\x04LOVE\x10\x03\x62\x06proto3')
)

_INTERACTIONLEVEL = _descriptor.EnumDescriptor(
  name='InteractionLevel',
  full_name='langame.protobuf.InteractionLevel',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='BAD', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='AVERAGE', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='GREAT', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='LOVE', index=3, number=3,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=544,
  serialized_end=605,
)
_sym_db.RegisterEnumDescriptor(_INTERACTIONLEVEL)

InteractionLevel = enum_type_wrapper.EnumTypeWrapper(_INTERACTIONLEVEL)
BAD = 0
AVERAGE = 1
GREAT = 2
LOVE = 3



_TOPIC = _descriptor.Descriptor(
  name='Topic',
  full_name='langame.protobuf.Topic',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='langame.protobuf.Topic.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='content', full_name='langame.protobuf.Topic.content', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=52,
  serialized_end=88,
)


_QUESTION = _descriptor.Descriptor(
  name='Question',
  full_name='langame.protobuf.Question',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='langame.protobuf.Question.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='content', full_name='langame.protobuf.Question.content', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='contexts', full_name='langame.protobuf.Question.contexts', index=2,
      number=3, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=90,
  serialized_end=147,
)


_TAG = _descriptor.Descriptor(
  name='Tag',
  full_name='langame.protobuf.Tag',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='langame.protobuf.Tag.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='content', full_name='langame.protobuf.Tag.content', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='score', full_name='langame.protobuf.Tag.score', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='human', full_name='langame.protobuf.Tag.human', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='question', full_name='langame.protobuf.Tag.question', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='generated', full_name='langame.protobuf.Tag.generated', index=5,
      number=6, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=149,
  serialized_end=250,
)


_USER = _descriptor.Descriptor(
  name='User',
  full_name='langame.protobuf.User',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='uid', full_name='langame.protobuf.User.uid', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='email', full_name='langame.protobuf.User.email', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='display_name', full_name='langame.protobuf.User.display_name', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='phone_number', full_name='langame.protobuf.User.phone_number', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='photo_url', full_name='langame.protobuf.User.photo_url', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='online', full_name='langame.protobuf.User.online', index=5,
      number=6, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='google', full_name='langame.protobuf.User.google', index=6,
      number=7, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='facebook', full_name='langame.protobuf.User.facebook', index=7,
      number=8, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='apple', full_name='langame.protobuf.User.apple', index=8,
      number=9, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='favourite_topics', full_name='langame.protobuf.User.favourite_topics', index=9,
      number=10, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='tag', full_name='langame.protobuf.User.tag', index=10,
      number=11, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='tokens', full_name='langame.protobuf.User.tokens', index=11,
      number=12, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=253,
  serialized_end=470,
)


_USERPREFERENCES = _descriptor.Descriptor(
  name='UserPreferences',
  full_name='langame.protobuf.UserPreferences',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='uid', full_name='langame.protobuf.UserPreferences.uid', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='unknown_people_recommendations', full_name='langame.protobuf.UserPreferences.unknown_people_recommendations', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=472,
  serialized_end=542,
)

DESCRIPTOR.message_types_by_name['Topic'] = _TOPIC
DESCRIPTOR.message_types_by_name['Question'] = _QUESTION
DESCRIPTOR.message_types_by_name['Tag'] = _TAG
DESCRIPTOR.message_types_by_name['User'] = _USER
DESCRIPTOR.message_types_by_name['UserPreferences'] = _USERPREFERENCES
DESCRIPTOR.enum_types_by_name['InteractionLevel'] = _INTERACTIONLEVEL
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Topic = _reflection.GeneratedProtocolMessageType('Topic', (_message.Message,), dict(
  DESCRIPTOR = _TOPIC,
  __module__ = 'langame.protobuf.langame_pb2'
  # @@protoc_insertion_point(class_scope:langame.protobuf.Topic)
  ))
_sym_db.RegisterMessage(Topic)

Question = _reflection.GeneratedProtocolMessageType('Question', (_message.Message,), dict(
  DESCRIPTOR = _QUESTION,
  __module__ = 'langame.protobuf.langame_pb2'
  # @@protoc_insertion_point(class_scope:langame.protobuf.Question)
  ))
_sym_db.RegisterMessage(Question)

Tag = _reflection.GeneratedProtocolMessageType('Tag', (_message.Message,), dict(
  DESCRIPTOR = _TAG,
  __module__ = 'langame.protobuf.langame_pb2'
  # @@protoc_insertion_point(class_scope:langame.protobuf.Tag)
  ))
_sym_db.RegisterMessage(Tag)

User = _reflection.GeneratedProtocolMessageType('User', (_message.Message,), dict(
  DESCRIPTOR = _USER,
  __module__ = 'langame.protobuf.langame_pb2'
  # @@protoc_insertion_point(class_scope:langame.protobuf.User)
  ))
_sym_db.RegisterMessage(User)

UserPreferences = _reflection.GeneratedProtocolMessageType('UserPreferences', (_message.Message,), dict(
  DESCRIPTOR = _USERPREFERENCES,
  __module__ = 'langame.protobuf.langame_pb2'
  # @@protoc_insertion_point(class_scope:langame.protobuf.UserPreferences)
  ))
_sym_db.RegisterMessage(UserPreferences)


# @@protoc_insertion_point(module_scope)
