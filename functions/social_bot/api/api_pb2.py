# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ava/v1/api.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.api import annotations_pb2 as google_dot_api_dot_annotations__pb2
from protoc_gen_openapiv2.options import annotations_pb2 as protoc__gen__openapiv2_dot_options_dot_annotations__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='ava/v1/api.proto',
  package='ava',
  syntax='proto3',
  serialized_options=b'Z\032github.com/langa-me/ava/v1\222Ac\0229\n\003Ava\"-\n\007langame\022\020https://langa.me\032\020contact@langa.me2\0031.0*\002\001\0022\020application/json:\020application/json',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x10\x61va/v1/api.proto\x12\x03\x61va\x1a\x1cgoogle/api/annotations.proto\x1a.protoc-gen-openapiv2/options/annotations.proto\",\n\x1a\x43onversationStarterRequest\x12\x0e\n\x06topics\x18\x01 \x03(\t\"K\n\x1b\x43onversationStarterResponse\x12\x1c\n\x14\x63onversation_starter\x18\x01 \x01(\t\x12\x0e\n\x06topics\x18\x02 \x03(\t2\xa3\x01\n\x1a\x43onversationStarterService\x12\x84\x01\n\x16GetConversationStarter\x12\x1f.ava.ConversationStarterRequest\x1a .ava.ConversationStarterResponse\"\'\x82\xd3\xe4\x93\x02!\"\x1c/v1/api/conversation/starter:\x01*B\x82\x01Z\x1agithub.com/langa-me/ava/v1\x92\x41\x63\x12\x39\n\x03\x41va\"-\n\x07langame\x12\x10https://langa.me\x1a\x10\x63ontact@langa.me2\x03\x31.0*\x02\x01\x02\x32\x10\x61pplication/json:\x10\x61pplication/jsonb\x06proto3'
  ,
  dependencies=[google_dot_api_dot_annotations__pb2.DESCRIPTOR,protoc__gen__openapiv2_dot_options_dot_annotations__pb2.DESCRIPTOR,])




_CONVERSATIONSTARTERREQUEST = _descriptor.Descriptor(
  name='ConversationStarterRequest',
  full_name='ava.ConversationStarterRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='topics', full_name='ava.ConversationStarterRequest.topics', index=0,
      number=1, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
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
  serialized_start=103,
  serialized_end=147,
)


_CONVERSATIONSTARTERRESPONSE = _descriptor.Descriptor(
  name='ConversationStarterResponse',
  full_name='ava.ConversationStarterResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='conversation_starter', full_name='ava.ConversationStarterResponse.conversation_starter', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='topics', full_name='ava.ConversationStarterResponse.topics', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
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
  serialized_end=224,
)

DESCRIPTOR.message_types_by_name['ConversationStarterRequest'] = _CONVERSATIONSTARTERREQUEST
DESCRIPTOR.message_types_by_name['ConversationStarterResponse'] = _CONVERSATIONSTARTERRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ConversationStarterRequest = _reflection.GeneratedProtocolMessageType('ConversationStarterRequest', (_message.Message,), {
  'DESCRIPTOR' : _CONVERSATIONSTARTERREQUEST,
  '__module__' : 'ava.v1.api_pb2'
  # @@protoc_insertion_point(class_scope:ava.ConversationStarterRequest)
  })
_sym_db.RegisterMessage(ConversationStarterRequest)

ConversationStarterResponse = _reflection.GeneratedProtocolMessageType('ConversationStarterResponse', (_message.Message,), {
  'DESCRIPTOR' : _CONVERSATIONSTARTERRESPONSE,
  '__module__' : 'ava.v1.api_pb2'
  # @@protoc_insertion_point(class_scope:ava.ConversationStarterResponse)
  })
_sym_db.RegisterMessage(ConversationStarterResponse)


DESCRIPTOR._options = None

_CONVERSATIONSTARTERSERVICE = _descriptor.ServiceDescriptor(
  name='ConversationStarterService',
  full_name='ava.ConversationStarterService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=227,
  serialized_end=390,
  methods=[
  _descriptor.MethodDescriptor(
    name='GetConversationStarter',
    full_name='ava.ConversationStarterService.GetConversationStarter',
    index=0,
    containing_service=None,
    input_type=_CONVERSATIONSTARTERREQUEST,
    output_type=_CONVERSATIONSTARTERRESPONSE,
    serialized_options=b'\202\323\344\223\002!\"\034/v1/api/conversation/starter:\001*',
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_CONVERSATIONSTARTERSERVICE)

DESCRIPTOR.services_by_name['ConversationStarterService'] = _CONVERSATIONSTARTERSERVICE

# @@protoc_insertion_point(module_scope)
