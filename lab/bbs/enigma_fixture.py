"""Explicit fixture dispatch and cached download namespace refresh."""
import sys


def refresh_download_context():
 import enigma_transfer
 for name in ('audio_download','prepare_audio_pressure_download','audit_audio_download'):
  module=sys.modules.get(name)
  if module:
   module.STORAGE=enigma_transfer.STORAGE;module.HELPER=enigma_transfer.HELPER
 module=sys.modules.get('audio_pressure_download')
 if module:
  module.HELPER=enigma_transfer.HELPER
  module.PressureDownload.HELPER=enigma_transfer.HELPER


def bind(lab,route):
 if route=='download':
  from enigma_sender_credit_instance import bind as selected
 else:
  assert route=='upload','Only declared transfer fixtures are supported'
  from enigma_receive_finish_instance import bind as selected
 context=selected(lab);refresh_download_context();return context


def from_result(result):
 context=result.get('server_fixture')
 if context and context.get('kind')=='sexyz-send-credit-eof-candidate':
  assert result.get('route','download')=='download'
  from enigma_sender_credit_instance import from_result as selected
 else:
  from enigma_receive_finish_instance import from_result as selected
 bound=selected(result);refresh_download_context();return bound
