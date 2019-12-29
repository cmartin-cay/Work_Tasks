import pandas as pd
from tkinter import filedialog

EUR_RATE = 1.102548658  # M
CAD_RATE = 1.32815  # D

# Read Initial Data. Store it for later use in saving the file

source_file = filedialog.askopenfilename(title="Select File")
orig_df = pd.read_excel(source_file)

# Formatting to strip ending spaces from SSS_DESC
orig_df["SSS_DESC"] = orig_df["SSS_DESC"].str.strip()
initial_cols = [
    "LE_DESC",
    "IP_ID",
    "IA_NAME",
    "ORDLG_NAV_DTE",
    "SPC_DESC",
    "SSS_DESC",
    "SPC_BASE_CURR_ISO",
    "ORDLG_TY_DESC",
    "ORD_FUND_NOTES",
    "ORDLG_INSTR_TY_DESC",
    "ORDLG_SHARES_VALUE",
    "ORDLG_NET_AMT",
    "ORD_STAT_DESC",
    "NAV_NET_VALUE",
    "IP_IS_NEW_ISSUE_ELIGIBLE",
    "ORD_TRANC_SUB_TY_DESC",
    "ORDLG_INVSTR_NOTES",
    "ORD_INV_REF",
    "ORDLG_CASH_DTE",
    "MINV_NAME",
    "ORD_TRANC_TY_DESC",
    "ORDLG_GROSS_AMT",
    "ORDLG_PROCEEDS_AMT",
    "CASH_AMT",
    "CASH_BAL",
    "SPC_ID",
    "MINV_ID",
    "IA_ID",
    "SSS_ID",
    "LEIA_ID",
    "ORD_RCVE_TMSTP",
    "ORDLG_DEALING_DTE",
    "ORDLG_STTL_DTE",
    "ORD_CREATED_DTE",
    "ORD_UPDATED_DTE",
]

# Create a copy of the data for working with
df = orig_df.copy()
df = df[initial_cols]

# Create the USD_CASH column and perform currency conversions
df["USD_CASH"] = df["ORDLG_NET_AMT"]
df.loc[df["SPC_BASE_CURR_ISO"] == "CAD", "USD_CASH"] = df["ORDLG_NET_AMT"] / CAD_RATE
df.loc[df["SPC_BASE_CURR_ISO"] == "EUR", "USD_CASH"] = df["ORDLG_NET_AMT"] * EUR_RATE

# Create a copy for the purpose of calculating only Subs and Reds (excluding CAD)
grouping_df = df.copy()
grouping_df = grouping_df.loc[
    (grouping_df["ORDLG_TY_DESC"].isin(["Subscription", "Redemption"]))
    & ~(grouping_df["SPC_DESC"].str.startswith("CLASS G"))
]
grouped = grouping_df.groupby(["LE_DESC", "SPC_BASE_CURR_ISO", "ORDLG_TY_DESC"])[
    "ORDLG_NET_AMT", "USD_CASH"
].sum()

# Create a copy for the purpose of calculating only Subs and Reds (CAD only)
cad_grouping_df = df.copy()
cad_grouping_df = cad_grouping_df.loc[
    (cad_grouping_df["ORDLG_TY_DESC"].isin(["Subscription", "Redemption"]))
    & (cad_grouping_df["SPC_DESC"].str.startswith("CLASS G"))
]
cad_grouped = cad_grouping_df.groupby(["LE_DESC", "SPC_DESC", "ORDLG_TY_DESC"])[
    "ORDLG_NET_AMT", "USD_CASH"
].sum()
rearranged_cols = [
    "LE_DESC",
    "IP_ID",
    "IA_NAME",
    "ORDLG_NAV_DTE",
    "SPC_DESC",
    "SSS_DESC",
    "SPC_BASE_CURR_ISO",
    "ORDLG_TY_DESC",
    "ORD_FUND_NOTES",
    "ORDLG_INSTR_TY_DESC",
    "ORDLG_SHARES_VALUE",
    "ORDLG_NET_AMT",
    "USD_CASH",
    "ORD_STAT_DESC",
    "NAV_NET_VALUE",
    "IP_IS_NEW_ISSUE_ELIGIBLE",
    "ORD_TRANC_SUB_TY_DESC",
    "ORDLG_INVSTR_NOTES",
    "ORD_INV_REF",
    "ORDLG_CASH_DTE",
    "MINV_NAME",
    "ORD_TRANC_TY_DESC",
    "ORDLG_GROSS_AMT",
    "ORDLG_PROCEEDS_AMT",
    "CASH_AMT",
    "CASH_BAL",
    "SPC_ID",
    "MINV_ID",
    "IA_ID",
    "SSS_ID",
    "LEIA_ID",
    "ORD_RCVE_TMSTP",
    "ORDLG_DEALING_DTE",
    "ORDLG_STTL_DTE",
    "ORD_CREATED_DTE",
    "ORD_UPDATED_DTE",
]
df = df[rearranged_cols]
df.sort_values(by=["LE_DESC", "SPC_DESC", "ORDLG_TY_DESC"], inplace=True)

height, width = df.shape
grouped_height, _ = grouped.shape

# Writing to Excel and formatting file output
save_file = filedialog.asksaveasfilename(filetypes=[("Excel", "*.xlsx")])
writer = pd.ExcelWriter(save_file, engine="xlsxwriter")
df.to_excel(writer, sheet_name="formatted", index=False, startrow=3)
grouped.to_excel(writer, sheet_name="formatted", startrow=height + 6, startcol=8)
cad_grouped.to_excel(
    writer,
    sheet_name="formatted",
    startrow=height + 6 + grouped_height + 1,
    startcol=8,
    header=False,
)

workbook = writer.book
worksheet = writer.sheets["formatted"]
worksheet.write(0, 0, "EUR")
worksheet.write(0, 1, EUR_RATE)
worksheet.write(1, 0, "CAD")
worksheet.write(1, 1, CAD_RATE)
cash_format = workbook.add_format({"num_format": "#,##0.00"})
shares_format = workbook.add_format({"num_format": "#,##0.0000"})
worksheet.set_column("A:A", 36)
worksheet.set_column("C:C", 52)
worksheet.set_column("D:I", 15)
worksheet.set_column("K:K", 18, shares_format)
worksheet.set_column("L:M", 18, cash_format)

orig_df.to_excel(writer, sheet_name="original", index=False)
report_settings = "report_settings.png"
worksheet2 = workbook.add_worksheet("report_settings")
worksheet2.insert_image(0, 0, report_settings)
writer.save()
