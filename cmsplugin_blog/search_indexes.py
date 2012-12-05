from haystack import indexes
from haystack import site
from cmsplugin_blog.models import Entry, EntryTitle
from cms.models.pluginmodel import CMSPlugin
from django.utils.encoding import force_unicode
import re

def _strip_tags(value):
    """
    Returns the given HTML with all tags stripped.

    This is a copy of django.utils.html.strip_tags, except that it adds some
    whitespace in between replaced tags to make sure words are not erroneously
    concatenated.
    """
    return re.sub(r'<[^>]*?>', ' ', force_unicode(value))

class BlogIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True)
    url = indexes.CharField(stored=True, indexed=False, model_attr='get_absolute_url')
    title = indexes.CharField(stored=True, indexed=False)
    pub_date = indexes.DateTimeField(model_attr='pub_date', null=True)

    def get_model(self):
        return Entry

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(is_published=True)

    def prepare_title(self, obj):
        return EntryTitle.objects.filter(entry=obj)[0]

    def prepare_text(self, obj):
        title = EntryTitle.objects.filter(entry=obj)[0]
        placeholder_plugins = CMSPlugin.objects.filter(placeholder__in=obj.placeholders.all())
        text = force_unicode(title)
        plugins = list(placeholder_plugins)
        for base_plugin in plugins:
            instance, plugin_type = base_plugin.get_plugin_instance()
            if instance is None:
                # this is an empty plugin
                continue
            if hasattr(instance, 'search_fields'):
                text += u' '.join(force_unicode(_strip_tags(getattr(instance, field, ''))) for field in instance.search_fields)
            if getattr(instance, 'search_fulltext', False) or getattr(plugin_type, 'search_fulltext', False):
                text += _strip_tags(instance.render_plugin(context=RequestContext(request))) + u' '
        return text



site.register(Entry, BlogIndex)
