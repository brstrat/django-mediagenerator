from django import template
from mediagenerator.generators.bundles.utils import _render_include_media
from mediagenerator import utils
from app.util.common import crunch
from django.template.base import resolve_variable, Template
register = template.Library()

class MediaNode(template.Node):
    def __init__(self, bundle, variation):
        self.bundle = bundle
        self.variation = variation

    def render(self, context):
        bundle = template.Variable(self.bundle).resolve(context)
        variation = {}
        for key, value in self.variation.items():
            variation[key] = template.Variable(value).resolve(context)

        if bundle == 'industry.css':
            industry = crunch(context.get('helper', {}).get('industry'))
            if industry:
                bundle = '%s_industry.css' % industry
            try:
                return _render_include_media(bundle, variation)
            except (KeyError, ValueError):
                pass
            return ''
        return _render_include_media(bundle, variation)

@register.tag
def include_media(parser, token):
    try:
        contents = token.split_contents()
        bundle = contents[1]
        variation_spec = contents[2:]
        variation = {}
        for item in variation_spec:
            key, value = item.split('=')
            variation[key] = value
    except (ValueError, AssertionError, IndexError):
        raise template.TemplateSyntaxError(
            '%r could not parse the arguments: the first argument must be the '
            'the name of a bundle in the MEDIA_BUNDLES setting, and the '
            'following arguments specify the media variation (if you have '
            'any) and must be of the form key="value"' % contents[0])

    return MediaNode(bundle, variation)

@register.simple_tag(takes_context=True)
def media_url_industry(context, url):
    try:
        industry = crunch(context.get('helper', {}).get('industry'))
        if industry:
            industry_url = 'img/industry/%s/%s' % (industry, url)
            return utils.media_url(industry_url)
    except KeyError:
        pass

    industry_url = 'img/industry/%s' % url
    return utils.media_url(industry_url)

@register.simple_tag(takes_context=True)
def media_url(context, url):
    url = Template(url).render(context)
    return utils.media_url(url)

@register.filter
def media_urls(url):
    return utils.media_urls(url)

@register.simple_tag    
def media_tooltip(media):
    if not media.is_embeddable:
        media_class = "media-download"
        media_name = "Download Media"
        url = media.url
        target_string = 'target="top"'
        return '<div class="dealLibraryMenu mediaItemTooltip"><span class="arrow"></span><a href="%s" %s class="%s bluebutton" >%s</a></div>'%(url, target_string, media_class, media_name)
    else:
        return ''
