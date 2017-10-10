#!/home/colin/work_tasks/bin/python

import numpy as np
import pandas as pd
from tkinter import filedialog
openfile = filedialog.askopenfilename()
df = pd.read_excel(openfile)
required_columns = ['Polar ID',
                    'Units',
                    'c',
                    'Security Description 1',
                    'Security Description 2',
                    'Cost',
                    'Market Value',
                    'M/E Price',
                    'Accrued Int/Dvd',
                    'Currency']

#Step 1 - Create a new sheet with only the columns I want
df1 = df[[*required_columns]]
#Make all of Security 2 into a text string and then strip start/end blanks
df1['Security Description 2'].fillna("", inplace=True)

#Combine the two Security Descriptions into one Name column
df1["Name"] = df1['Security Description 1'] +" " + df1['Security Description 2'].map(str)
df1.fillna(0, inplace=True)

#Re-order the columns
required_columns = ['Polar ID',
                    'Units',
                    'c',
                    'Name',
                    'Market Value',
                    'M/E Price',
                    'Accrued Int/Dvd',
                    'Currency']

#Create a pivot table to flatten duplicates then convert back to Dataframe
piv_table = pd.pivot_table(df1,
                           index=["Polar ID", "c", "Name", "M/E Price", "Currency"],
                           values=['Units', 'Market Value', 'Accrued Int/Dvd'],
                           aggfunc=np.sum)
df2 = pd.DataFrame(piv_table.to_records())
df2 = df2[[*required_columns]]

#
# #Strip out all unwanted funds
# df2 = df2[(df2['PortNameAlt'].str[-1].str.isdigit()) | (df2['PortNameAlt'] == "PMSLSF")]
#
# Set the Market value to exclude all small amounts
mv_eq = (df2['Market Value'] < -0.25) | (df2['Market Value'] > 0.25)
#
# Set the accrual value to exclude all small amounts
ac_eq = (df2['Accrued Int/Dvd'] < -0.25) | (df2['Accrued Int/Dvd'] > 0.25)
#
# Filter rule. Exclude zero quantity. Exclude small MV's and Accrual's
df2 = df2[(df2['Units'] != 0) | (mv_eq) | (ac_eq)]
#
savefile = filedialog.asksaveasfilename()
writer = pd.ExcelWriter(savefile)
# piv_table.to_excel(writer)
df2.to_excel(writer, index=False, sheet_name='Pasting')
df1.to_excel(writer, index=False, sheet_name='Original')
writer.save()
