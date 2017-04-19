# -*- coding: utf-8 -*-
# !/usr/bin/env python

import gettext
import six


class TranslatorFactory(object):
    def __init__(self, domain='i18n', localedir='./locale'):
        self.domain = domain
        self.localedir = localedir

    def _make_translation_func(self, domain='i18n'):
        t = gettext.translation(self.domain,
                                self.localedir,
                                languages=['zh_CN'],
                                fallback=True)
        m = t.gettext if six.PY3 else t.ugettext

        return m

    def primary(self, msg):
        return self._make_translation_func()(msg)


_translator = TranslatorFactory()
_ = _translator.primary
