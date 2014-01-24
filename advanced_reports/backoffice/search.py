def convert_to_raw_tsquery(query):
    words = query.split()
    prefixed_words = (u'%s:*' % word for word in words)
    return u' & '.join(prefixed_words)
