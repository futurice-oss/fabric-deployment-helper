import string, copy, re, copy

def is_ascii_letters(s, bucket):
    return all(c in bucket for c in s)

ALLOWED_CHARS = string.ascii_letters + '_.'
def escape_bad_matches(s):
    for match in re.findall('{(.+?)}', s):
        if not is_ascii_letters(match, ALLOWED_CHARS):
            match = re.escape(match)
            s = re.sub('({0})'.format(match),
                    r'{\1}', s)
    return s

def fmtkeys(s):
    return [k[1] for k in string.Formatter().parse(s) if k[1]]

def formatloc(s, ctx={}, **kwargs):
    """ Lazy evaluation for strings """
    if not isinstance(s, basestring) and not callable(s):
        return s
    for times in range(6):
        kw = {}
        # adds values to interpolated values with defaults
        if isinstance(s, basestring):
            kw.update(**{k[1]: '' for k in string.Formatter().parse(s) if k[1] and '.' not in k[1]})
            # escape non-ascii matches before .format()
            s = escape_bad_matches(s)
            if '{' not in s:
                break
        keys = kw.keys()
        for key in keys:
            kw.update({key: getattr(ctx, key, '{{{0}}}'.format(key))})

        kw.update(**ctx)
        kw.update(**kwargs)
        
        # resolve functions
        for k,v in kw.iteritems():
            if k in keys:
                if callable(v):
                    kw[k] = v(kw)
        try:
            if callable(s):
                s = s(kw)
            else:
                if isinstance(s, basestring):
                    s = s.replace('{}','{{}}')
                    s = s.format(**kw)
        except IndexError, e:
            raise KeyError
    return s
