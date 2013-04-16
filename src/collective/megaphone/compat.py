try:
    from zope.component.hooks import getSite, setSite, setHooks
except ImportError:
    try:
        from zope.site.hooks import getSite, setSite, setHooks
    except ImportError:
        from zope.app.component.hooks import getSite, setSite, setHooks

try:
    from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
except ImportError:
    from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

try:
	from zope.browser.interfaces import IAdding
except ImportError:
	from zope.app.container.interfaces import IAdding
