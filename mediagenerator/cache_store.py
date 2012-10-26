from django.db import models

try:
    import cPickle as pickle
except ImportError:
    import pickle

import os 

# {file path: mtime}
_cache_store = {}

class __MediageneratorCacheStore(models.Model):
    media = models.TextField(default='')

    class Meta:
        db_table = '_mediagenerator_cache_store'

    @classmethod    
    def getmtime(cls, path):
        return _cache_store.get(path)

    @classmethod
    def setmtime(cls, path):
        global _cache_store

        _cache_store[path] = os.path.getmtime(path)

        return cls.getmtime(path)

    @classmethod
    def delmtime(cls, path):
        global _cache_store
        return bool(_cache_store.pop(path, None))

    @classmethod
    def mtime_modified(cls, path):
        global _cache_store
        mtime = os.path.getmtime(path)
        is_modified = mtime != cls.getmtime(path)
        _cache_store[path] = mtime
        return is_modified

    @classmethod
    def clear_cache(cls):
        global _cache_store

        _cache_store = {}
        cls.objects.all().delete()

    @classmethod
    def load_cache(cls):
        global _cache_store

        if not _cache_store:
            try:
                cache_store = cls.objects.get()
                _cache_store = pickle.loads(str(cache_store.media)) or {}
            except cls.DoesNotExist:
                _cache_store = {}

    @classmethod
    def save_cache(cls):
        pickled_cache = pickle.dumps(_cache_store)
        try:
            cache_store = cls.objects.get()
            cache_store.media = pickled_cache
        except cls.DoesNotExist:
            cache_store = cls(media=pickled_cache)

        cache_store.save()

getmtime = __MediageneratorCacheStore.getmtime
setmtime = __MediageneratorCacheStore.setmtime
delmtime = __MediageneratorCacheStore.delmtime
mtime_modified = __MediageneratorCacheStore.mtime_modified
clear_cache = __MediageneratorCacheStore.clear_cache
load_cache = __MediageneratorCacheStore.load_cache
save_cache = __MediageneratorCacheStore.save_cache
