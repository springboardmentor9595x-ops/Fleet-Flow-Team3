from app.main import app
schema = app.openapi()
paths = sorted(schema.get('paths', {}).keys())
print(f'Total paths: {len(paths)}')
for p in paths:
    methods = sorted(schema['paths'][p].keys())
    m_str = ' '.join(m.upper() for m in methods)
    print(f'  {m_str:30} {p}')
