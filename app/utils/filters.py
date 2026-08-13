def to_iso_filter(dt):
    if not dt:
        return ''
    return dt.isoformat()