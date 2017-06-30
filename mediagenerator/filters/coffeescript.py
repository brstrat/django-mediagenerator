import settings
from django.utils.encoding import smart_str
from hashlib import sha1
from mediagenerator.generators.bundles.base import Filter
from mediagenerator.utils import find_file, read_text_file
from mediagenerator import cache_store
import subprocess
import os
import sys

class CoffeeScript(Filter):
    takes_input = False

    def __init__(self, **kwargs):
        self.config(kwargs, module=None)
        super(CoffeeScript, self).__init__(**kwargs)
        assert self.filetype == 'js', (
            'CoffeeScript only supports compilation to js. '
            'The parent filter expects "%s".' % self.filetype)

        self._compiled = None
        self._compiled_hash = None
        self.path = None

    @classmethod
    def from_default(cls, name):
        return {'module': name}

    def get_output(self, variation):
        self._regenerate(debug=False)
        yield self._compiled

    def get_dev_output(self, name, variation):
        assert name == self.module
        self._regenerate(debug=True)
        return self._compiled

    def get_dev_output_names(self, variation):
        self._regenerate(debug=True)
        yield self.module, self._compiled_hash

    def _regenerate(self, debug=False):
        self.path = self.path or find_file(self.module)
        is_modified = cache_store.mtime_modified(self.path)
        self._compiled = self._compile(debug=debug, from_cache=not is_modified)

        self._compiled_hash = sha1(smart_str(self._compiled)).hexdigest()

    def _compile(self, debug=False, from_cache=False):
        try:
            coffee_file = self.path
            js_file = self.path.replace('.coffee', '.js')

            if from_cache or settings.DEV_FAST_START:
                if os.path.exists(js_file):
                    return read_text_file(js_file)

            # subprocess broken in appengine sandbox
            if not settings.DEV_GENERATE_MEDIA:
                return read_text_file(js_file)

            shell = sys.platform == 'win32'
            run = ['coffee', '--bare', '--compile']
            run.append(coffee_file)
            subprocess.check_output(run, shell=shell, universal_newlines=True, stderr=subprocess.STDOUT)

            return read_text_file(js_file)

            """
            output, error = cmd.communicate(smart_str(input))
            assert cmd.wait() == 0, ('CoffeeScript command returned bad '
                                     'result:\n%s' % error)
            return output.decode('utf-8')
            """
        except Exception, e:
            cache_store.delmtime(self.path)
            err = getattr(e, 'output', e)
            raise ValueError("Failed to run CoffeeScript compiler for this "
                "file. Please confirm that the \"coffee\" application is "
                "on your path and that you can run it from your own command "
                "line.\n"
                "Error was: %s" % err)
