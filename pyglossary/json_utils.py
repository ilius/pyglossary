import sys
try:
    import json
except ImportError:
    import simplejson as json

from collections import OrderedDict


def dataToPrettyJson(data, ensure_ascii=False, sort_keys=False):
    return json.dumps(
        data,
        sort_keys=sort_keys,
        indent=2,
        ensure_ascii=ensure_ascii,
    )


def dataToCompactJson(data, ensure_ascii=False, sort_keys=False):
    return json.dumps(
        data,
        sort_keys=sort_keys,
        separators=(',', ':'),
        ensure_ascii=ensure_ascii,
    )


jsonToData = json.loads


def jsonToOrderedData(text):
    return json.JSONDecoder(
        object_pairs_hook=OrderedDict,
    ).decode(text)

###############################


def loadJsonConf(module, confPath, decoders={}):
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
        try:
            decoder = decoders[param]
        except KeyError:
            pass
        else:
            value = decoder(value)
        setattr(module, param, value)


def saveJsonConf(module, confPath, params, encoders={}):
    if isinstance(module, str):
        module = sys.modules[module]
    ###
    data = OrderedDict()
    for param in params:
        value = getattr(module, param)
        try:
            encoder = encoders[param]
        except KeyError:
            pass
        else:
            value = encoder(value)
        data[param] = value
    ###
    text = dataToPrettyJson(data)
    try:
        open(confPath, 'w').write(text)
    except Exception as e:
        print('failed to save file "%s": %s' % (confPath, e))
        return


def loadModuleJsonConf(module):
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


def saveModuleJsonConf(module):
    if isinstance(module, str):
        module = sys.modules[module]
    ###
    saveJsonConf(
        module,
        module.confPath,
        module.confParams,
        getattr(module, 'confEncoders', {}),
    )
