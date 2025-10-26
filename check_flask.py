try:
    import flask
    print('FOUND', flask)
except Exception as e:
    print('IMPORT_ERROR', e)
