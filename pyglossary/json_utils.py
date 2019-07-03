import sys
try:
	import json
except ImportError:
	import simplejson as json

from collections import OrderedDict

from typing import (
	Union,
	Dict,
	List,
	AnyStr,
	Optional,
)
from types import ModuleType

JsonEncodable = Union[Dict, List]
# OrderedDict is also subclass of Dict, issubclass(OrderedDict, Dict) == True

def dataToPrettyJson(
	data: JsonEncodable,
	ensure_ascii: bool = False,
	sort_keys: bool = False,
):
	return json.dumps(
		data,
		sort_keys=sort_keys,
		indent=2,
		ensure_ascii=ensure_ascii,
	)


def dataToCompactJson(
	data: JsonEncodable,
	ensure_ascii: bool = False,
	sort_keys: bool = False,
) -> str:
	return json.dumps(
		data,
		sort_keys=sort_keys,
		separators=(',', ':'),
		ensure_ascii=ensure_ascii,
	)


def jsonToData(st: AnyStr) -> JsonEncodable:
	return json.loads(st)


def jsonToOrderedData(text: str) -> OrderedDict:
	return json.JSONDecoder(
		object_pairs_hook=OrderedDict,
	).decode(text)

###############################


def loadJsonConf(module: Union[ModuleType, str], confPath: str, decoders: Optional[Dict] = None) -> None:
	from os.path import isfile
	###
	if not isfile(confPath):
		return
	###
	try:
		text = open(confPath).read()
	except Exception as e:
		print('failed to read file "%s": %s' % (confPath, e))
		return
	###
	try:
		data = json.loads(text)
	except Exception as e:
		print('invalid json file "%s": %s' % (confPath, e))
		return
	###
	if isinstance(module, str):
		module = sys.modules[module]
	for param, value in data.items():
		if decoders:
			decoder = decoders.get(param)
			if decoder is not None:
				value = decoder(value)
		setattr(module, param, value)


def saveJsonConf(module: Union[ModuleType, str], confPath: str, params: str, encoders: Optional[Dict] = None) -> None:
	if isinstance(module, str):
		module = sys.modules[module]
	###
	data = OrderedDict()
	for param in params:
		value = getattr(module, param)
		if encoders:
			encoder = encoders.get(param)
			if encoder is not None:
				value = encoder(value)
		data[param] = value
	###
	text = dataToPrettyJson(data)
	try:
		open(confPath, 'w').write(text)
	except Exception as e:
		print('failed to save file "%s": %s' % (confPath, e))
		return


def loadModuleJsonConf(module: Union[ModuleType, str]) -> None:
	if isinstance(module, str):
		module = sys.modules[module]
	###
	decoders = getattr(module, 'confDecoders', {})
	###
	try:
		sysConfPath = module.sysConfPath
	except AttributeError:
		pass
	else:
		loadJsonConf(
			module,
			sysConfPath,
			decoders,
		)
	####
	loadJsonConf(
		module,
		module.confPath,
		decoders,
	)
	# should use module.confParams to restrict json keys? FIXME


def saveModuleJsonConf(module: Union[ModuleType, str]) -> None:
	if isinstance(module, str):
		module = sys.modules[module]
	###
	saveJsonConf(
		module,
		module.confPath,
		module.confParams,
		getattr(module, 'confEncoders', {}),
	)
