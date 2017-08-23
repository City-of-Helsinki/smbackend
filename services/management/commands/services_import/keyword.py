from django.conf import settings

from services.models import Keyword


class KeywordHandler():

    def __init__(self, verbosity=False, logger=None):
        self.supported_languages = [l[0] for l in settings.LANGUAGES]
        self.keywords = self._keywords()
        self.keywords_by_id = self._keywords_by_id()
        self.verbosity = verbosity
        self.logger = logger

    def _keywords(self):
        keywords = {}
        for lang in self.supported_languages:
            kw_list = Keyword.objects.filter(language=lang)
            kw_dict = {kw.name: kw for kw in kw_list}
            keywords[lang] = kw_dict
        return keywords

    def _keywords_by_id(self):
        return {kw.pk: kw for kw in Keyword.objects.all()}

    def _save_searchwords(self, obj, info, language):
        field_name = 'extra_searchwords_%s' % language
        new_kw_set = set()
        if field_name in info:
            kws = [x.strip() for x in info[field_name].split(',')]
            kws = [x for x in kws if x]
            new_kw_set = set()
            for kw in kws:
                if kw not in self.keywords[language]:
                    kw_obj = Keyword(name=kw, language=language)
                    kw_obj.save()
                    self.keywords[language][kw] = kw_obj
                    self.keywords_by_id[kw_obj.pk] = kw_obj
                else:
                    kw_obj = self.keywords[language][kw]
                new_kw_set.add(kw_obj.pk)
        return new_kw_set

    def sync_searchwords(self, obj, info, obj_changed):
        new_keywords = set()
        for lang in self.supported_languages:
            new_keywords |= self._save_searchwords(obj, info, lang)

        old_kw_set = set(obj.keywords.all().values_list('pk', flat=True))
        if old_kw_set == new_keywords:
            return obj_changed

        if self.verbosity and self.logger:
            old_kw_str = ', '.join([self.keywords_by_id[x].name for x in old_kw_set])
            new_kw_str = ', '.join([self.keywords_by_id[x].name for x in new_keywords])
            self.logger.info(
                "%s keyword set changed: %s -> %s" % (obj, old_kw_str, new_kw_str))
        obj.keywords = list(new_keywords)
        return True
