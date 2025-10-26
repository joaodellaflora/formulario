import pandas as pd
from pathlib import Path
p = Path('ferramenta_ghg_protocol_v2025.0.1 (1).xlsx')
if not p.exists():
    p = Path('Fatores de emissão.xlsx')
print('Using', p)
df = pd.read_excel(p, sheet_name='Combustão móvel', header=None)
# print first 20 rows with index
pd.set_option('display.max_columns', None)
print('\n=== RAW FIRST 20 ROWS ===')
print(df.head(20).to_string(index=True))
# try to show the first 5 rows transposed to see long headers
print('\n=== TRANSPOSED HEADERS (first 10 columns) ===')
print(df.iloc[:10,:10].T.to_string())
# detect header row as used by extractor
best_i = 0; best_cnt = -1
for i in range(min(12, len(df))):
    cnt = df.iloc[i].count()
    if cnt > best_cnt:
        best_cnt = cnt; best_i = i
print('\nDetected header row index:', best_i, 'non-null count:', best_cnt)
header = df.iloc[best_i].fillna('').astype(str).str.strip().tolist()
print('\n=== DETECTED HEADER (first 100 chars each) ===')
for i,h in enumerate(header[:40]):
    print(i, repr(h)[:100])
# show the next 10 rows using that header
data = df.iloc[best_i+1:best_i+11].copy()
data.columns = header
print('\n=== SAMPLE DATA (using detected header) ===')
print(data.head(10).to_string())
