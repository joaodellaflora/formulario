import pandas as pd
path = 'Fatores de emissão.xlsx'
xls = pd.read_excel(path, sheet_name=None)
print('SHEETS:', list(xls.keys()))
def show(name):
    print('\n--- SHEET:', name)
    df = xls[name]
    print(df.head(5).to_string(index=False))

for candidate in ['Todos os combustiveis','Composição combustíveis','Balsa','Transporte Onibus']:
    if candidate in xls:
        show(candidate)
    else:
        # show first 3 sheets if candidate not present
        pass

print('\n-- First sheet preview --')
first = list(xls.keys())[0]
print(first)
print(xls[first].head(10).to_string(index=False))
