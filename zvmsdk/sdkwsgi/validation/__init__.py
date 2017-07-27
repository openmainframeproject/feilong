#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import functools
import re

import jsonschema
from jsonschema import exceptions as jsonschema_exc
import six

from zvmsdk import exception


def _schema_validation_helper(schema, target, args, kwargs, is_body=True):
    schema_validator = _SchemaValidator(
        schema, is_body)
    schema_validator.validate(target)


def schema(request_body_schema):

    def add_validator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _schema_validation_helper(request_body_schema, kwargs['body'],
                                      args, kwargs)
            return func(*args, **kwargs)
        return wrapper

    return add_validator


class FormatChecker(jsonschema.FormatChecker):

    def check(self, instance, format):

        if format not in self.checkers:
            return

        func, raises = self.checkers[format]
        result, cause = None, None

        try:
            result = func(instance)
        except raises as e:
            cause = e
        if not result:
            msg = "%r is not a %r" % (instance, format)
            raise jsonschema_exc.FormatError(msg, cause=cause)


class _SchemaValidator(object):
    """A validator class

    This class is changed from Draft4Validator to validate minimum/maximum
    value of a string number(e.g. '10'). This changes can be removed when
    we tighten up the API definition and the XML conversion.
    Also FormatCheckers are added for checking data formats which would be
    passed through nova api commonly.

    """
    validator = None
    validator_org = jsonschema.Draft4Validator

    def __init__(self, schema, relax_additional_properties=False,
                 is_body=True):
        self.is_body = is_body

        validators = {
            'dummy': self._dummy
        }

        validator_cls = jsonschema.validators.extend(self.validator_org,
                                                     validators)

        format_checker = FormatChecker()
        self.validator = validator_cls(schema, format_checker=format_checker)

    def _dummy(self, validator, minimum, instance, schema):
        pass

    def validate(self, *args, **kwargs):
        try:
            self.validator.validate(*args, **kwargs)
        except jsonschema.ValidationError as ex:
            if isinstance(ex.cause, exception.InvalidName):
                detail = ex.cause.format_message()
            elif len(ex.path) > 0:
                if self.is_body:
                    # NOTE: For whole OpenStack message consistency, this error
                    #       message has been written as the similar format of
                    #       WSME.
                    detail = ("Invalid input for field/attribute %(path)s. "
                              "Value: %(value)s. %(message)s")
                else:
                    detail = ("Invalid input for query parameters %(path)s. "
                              "Value: %(value)s. %(message)s")
                detail = detail % {
                    'path': ex.path.pop(), 'value': ex.instance,
                    'message': ex.message
                }
            else:
                detail = ex.message
            raise exception.ValidationError(detail=detail)
        except TypeError as ex:
            # NOTE: If passing non string value to patternProperties parameter,
            #       TypeError happens. Here is for catching the TypeError.
            detail = six.text_type(ex)
            raise exception.ValidationError(detail=detail)


def _remove_unexpected_query_parameters(schema, req):
    """Remove unexpected properties from the req.GET."""
    additional_properties = schema.get('addtionalProperties', True)

    if additional_properties:
        pattern_regexes = []

        patterns = schema.get('patternProperties', None)
        if patterns:
            for regex in patterns:
                pattern_regexes.append(re.compile(regex))

        for param in set(req.GET.keys()):
            if param not in schema['properties'].keys():
                if not (list(regex for regex in pattern_regexes if
                             regex.match(param))):
                    del req.GET[param]


def query_schema(query_params_schema, min_version=None,
                 max_version=None):
    """Register a schema to validate request query parameters."""

    def add_validator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if 'req' in kwargs:
                req = kwargs['req']
            else:
                req = args[1]

            if _schema_validation_helper(query_params_schema,
                                         req.GET.dict_of_lists(),
                                         args, kwargs, is_body=False):
                _remove_unexpected_query_parameters(query_params_schema, req)
            return func(*args, **kwargs)
        return wrapper

    return add_validator
