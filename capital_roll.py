import pandas as pd
import numpy as np

# SHORT_NAME = {"PMSF": "POLAR MULTI-STRATEGY FUND", "PMSFL": "POLAR MULTI-STRATEGY FUND (LEGACY)",

#               "PMSFUSLP": "POLAR MULTI-STRATEGY FUND (US) LP"}

CAD_RATE = 1 / 1.32385

SHORT_NAME = {
    "PMSF": "POLAR MULTI-STRATEGY FUND",
    "PMSFUSLP": "POLAR MULTI-STRATEGY FUND (US) LP",
}

pmsf_file = "P:\Work Tasks\PMSF Axi.xlsx"
pmsfl_file = "P:\Work Tasks\PMSFL Axi.xlsx"
pmsfuslp_file = "P:\Work Tasks\PMSFUSLP Axi.xlsx"
capital_file = "P:\Work Tasks\PMSF Subs.xlsx"

# FILE_LOCATIONS = {"PMSF": pmsf_file, "PMSFL": pmsfl_file, "PMSFUSLP": pmsfuslp_file}
FILE_LOCATIONS = {"PMSF": pmsf_file, "PMSFUSLP": pmsfuslp_file}


def read_closing_axi(file_location, fund_name):
    # Read in the prior month AXI closing file
    df = pd.read_excel(
        file_location,
        header=8,
        usecols=[
            "ID",
            "Type",
            "Description",
            "Currency",
            "New Issue Eligible",
            "Closing Net Assets LE CCY",
            "Accrued Incentive Fee",
            "New Issue P/L",
        ],
    )

    # Accrued Incentive needs to be positive for later workings
    df["Accrued Incentive Fee"] = df["Accrued Incentive Fee"] * -1

    # US LP has different identifiers which need to be taken into account
    if fund_name == "PMSFUSLP":
        df["SPC_DESC"] = df["ID"]
        df = df.loc[df["Type"] == "LEIA"]
    else:
        # We need an identifier that is only on the SPC lines
        df.loc[df["Type"] == "SPC", "SPC_DESC"] = df["Description"]
        df.fillna(method="ffill", inplace=True)
        df = df.loc[df["Type"] == "SSS"]

    # US LP axi sheet does not identify New Issue status. Calculate it based on New Issue PL
    # This method will not work if there is a month without New Issue Income

    # TODO Identify a better method for assiging US LP new issue incomes
    if fund_name == "PMSFUSLP":
        df["New Issue Eligible"] = "N"
        df.loc[df["New Issue P/L"] != 0, "New Issue Eligible"] = "Y"
    df.drop("Type", axis=1, inplace=True)

    # Simple formatting insructions
    rearranged_columns = [
        "New Issue Eligible",
        "ID",
        "SPC_DESC",
        "Description",
        "Currency",
        "Accrued Incentive Fee",
        "Closing Net Assets LE CCY",
    ]

    df = df[rearranged_columns]
    df["New Issue Eligible"] = df["New Issue Eligible"].replace({"Y": "Yes", "N": "No"})
    df.set_index("ID", inplace=True)
    return df


def read_opening_capital_activity(file_location, fund_name):
    # Read in the already formatted Opening Capital Activty File
    df_capital = pd.read_excel(
        file_location,
        header=3,
        usecols=[
            "LE_DESC",
            "SPC_DESC",
            "SSS_DESC",
            "SPC_BASE_CURR_ISO",
            "ORDLG_TY_DESC",
            "USD_CASH",
            "IP_IS_NEW_ISSUE_ELIGIBLE",
            "SSS_ID",
            "LEIA_ID",
        ],
    )

    if fund_name == "PMSFUSLP":
        df_capital["SPC_DESC"] = df_capital["LEIA_ID"]
        df_capital["SSS_ID"] = df_capital["LEIA_ID"]
        df_capital.drop("LEIA_ID", axis=1, inplace=True)

    df_capital.rename(
        columns={
            "IP_IS_NEW_ISSUE_ELIGIBLE": "New Issue Eligible",
            "SSS_ID": "ID",
            "SSS_DESC": "Description",
            "SPC_BASE_CURR_ISO": "Currency",
        },
        inplace=True,
    )

    # Identify only the lines that represent the fund we are looking for. This will strip out all the information that we don't want
    # or need from the Opening Capital File
    df_capital = df_capital.loc[df_capital["LE_DESC"] == SHORT_NAME[fund_name]]
    df_capital.drop("LE_DESC", axis=1, inplace=True)

    # TODO Flag for each fund name

    if fund_name == "PMSFL":
        # Opening Capital Sheet is in USD. This needs to be converted to CAD for Legacy only
        df_capital["USD_CASH"] = df_capital["USD_CASH"] / CAD_RATE
        print(f"Legacy {df_capital}")

    # Include Subs and Reds Column (drop transfers)
    df_capital.loc[
        df_capital["ORDLG_TY_DESC"].isin(["Subscription", "Switch In"]), "Subscription"
    ] = df_capital["USD_CASH"]

    df_capital.loc[
        df_capital["ORDLG_TY_DESC"].isin(["Redemption", "Switch Out"]), "Redemption"
    ] = df_capital["USD_CASH"]

    df_capital.drop(["ORDLG_TY_DESC", "USD_CASH"], axis=1, inplace=True)

    # Group individual subs/reds/switches into per Series
    df_capital = (
        df_capital.groupby(
            ["ID", "SPC_DESC", "Description", "New Issue Eligible", "Currency"]
        )
        .sum(min_count=1)
        .reset_index()
    )

    df_capital.set_index("ID", inplace=True)
    return df_capital


def merge_closing_and_capital(closing, capital, fund_name):
    df_merged = closing.merge(
        capital,
        on=["ID", "SPC_DESC", "Description", "New Issue Eligible", "Currency"],
        how="outer",
    )

    df_merged.reset_index(inplace=True)
    df_merged.sort_values(["SPC_DESC", "ID"], inplace=True)

    # Format to include required columns to match Excel
    df_merged["Guaranteed Perf Fees"] = (
        df_merged["Redemption"]
        / df_merged["Closing Net Assets LE CCY"]
        * df_merged["Accrued Incentive Fee"]
    )

    # df_merged.fillna(0, inplace=True)
    df_merged["CAD Adjusted Open Equity"] = np.nan
    if fund_name == "PMSFL":
        df_merged["CAD Adjusted Open Equity"] = df_merged[
            [
                "Closing Net Assets LE CCY",
                "Accrued Incentive Fee",
                "Subscription",
                "Redemption",
                "Guaranteed Perf Fees",
            ]
        ].sum(axis=1)

    df_merged["Adjusted Opening Equity"] = df_merged[
        [
            "Closing Net Assets LE CCY",
            "Accrued Incentive Fee",
            "Subscription",
            "Redemption",
            "Guaranteed Perf Fees",
        ]
    ].sum(axis=1)

    if fund_name == "PMSFL":
        df_merged["Adjusted Opening Equity"] = (
            df_merged["Adjusted Opening Equity"] * CAD_RATE
        )
    df_merged.loc[df_merged["New Issue Eligible"] == "Yes", "NR"] = df_merged[
        "Adjusted Opening Equity"
    ]
    df_merged.loc[df_merged["New Issue Eligible"] == "No", "R"] = df_merged[
        "Adjusted Opening Equity"
    ]
    new_order = [
        "ID",
        "SPC_DESC",
        "Description",
        "Closing Net Assets LE CCY",
        "Subscription",
        "Redemption",
        "Accrued Incentive Fee",
        "Guaranteed Perf Fees",
        "CAD Adjusted Open Equity",
        "Adjusted Opening Equity",
        "NR",
        "R",
    ]
    df_merged = df_merged[new_order]
    return df_merged


def write_excel_sheet(dataframe, fund_name, writer):
    # Writing to Excel and formatting file output
    dataframe.to_excel(writer, sheet_name=fund_name, index=False)
    workbook = writer.book
    worksheet = writer.sheets[fund_name]
    cash_format = workbook.add_format({"num_format": "#,##0.00"})
    worksheet.set_column("A:C", 17)
    worksheet.set_column("D:L", 20, cash_format)


# df1 = read_closing_axi(pmsfl_file, fund_name="PMSFL")

# df2 = read_opening_capital_activity(capital_file, fund_name="PMSFL")

# pmsf = merge_closing_and_capital(df1, df2, fund_name="PMSFL")

# write_excel_sheet(pmsf, "PMSFL")


def main():
    writer = pd.ExcelWriter("Capital Example.xlsx", engine="xlsxwriter")
    for fund_name in SHORT_NAME.keys():
        df1 = read_closing_axi(FILE_LOCATIONS[fund_name], fund_name)
        df2 = read_opening_capital_activity(capital_file, fund_name)
        merged = merge_closing_and_capital(df1, df2, fund_name)
        write_excel_sheet(merged, fund_name, writer=writer)
    writer.save()


main()
