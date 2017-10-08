#!/home/colin/work_tasks/bin/python

# import numpy as np
import pandas as pd
from tkinter import filedialog
openfile = filedialog.askopenfilename()
df = pd.read_excel(openfile)
required_columns = ['Polar ID',
                    'Units',
                    'Security Description 1',
                    'Cost',
                    'Market Value',
                    'M/E Price',
                    'Accrued Int/Dvd',
                    'Currency']

#Step 1 - Create a new sheet with only the columns I want
df1 = df[[*required_columns]]
print(df1.head())

# df2 = df1.copy()
#
# #Strip out all unwanted funds
# df2 = df2[(df2['PortNameAlt'].str[-1].str.isdigit()) | (df2['PortNameAlt'] == "PMSLSF")]
#
# # Set the Market value to exclude all small amounts
# mv_eq = (df2['SumOfMarket Value'] < -0.25) | (df2['SumOfMarket Value'] > 0.25)
#
# # Set the accrual value to exclude all small amounts
# ac_eq = (df2['SumOfEnding Accrued'] < -0.25) | (df2['SumOfEnding Accrued'] > 0.25)
#
# # Filter rule. Exclude zero quantity. Exclude small MV's and Accrual's
# df2 = df2[(df2['SumOfUnits'] != 0) | (mv_eq) | (ac_eq)]
#
# savefile = filedialog.asksaveasfilename()
# writer = pd.ExcelWriter(savefile)
# df2.to_excel(writer, index=False, sheet_name='Pasting')
# df1.to_excel(writer, index=False, sheet_name='Original')
# writer.save()
