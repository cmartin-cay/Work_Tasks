import pandas as pd
from tkinter.filedialog import askopenfilename


def open_gtrades():
    location = askopenfilename(
        title="Open the Class G AXI Allocation",
        filetypes=(
            ("Excel Files", "*.xlsx"),
            ("Excel 2000", "*.xls"),
            ("all files", "*.*"),
        ),
    )
    cols = [
        "SSS_ID",
        "ORDLG_SHARES_VALUE",
        "NAV_NET_VALUE",
        "TRADE DATE",
        "ORDLG_TY_DESC",
    ]
    res = pd.read_excel(location, usecols=cols)
    return res


def open_lookup():
    location = askopenfilename(
        title="Open the Lookup File",
        filetypes=(
            ("Excel Files", "*.xlsx"),
            ("Excel 2000", "*.xls"),
            ("all files", "*.*"),
        ),
    )
    return pd.read_excel(location)


def initial_merge_and_group(g_file, lookup):
    res = pd.merge(g_file, lookup, on="SSS_ID")

    # Convert Sub/Red/Switch to Buy or Sell
    res.loc[
        res["ORDLG_TY_DESC"].isin(["Subscription", "Switch In"]), "Buy_Sell_Short_Cover"
    ] = "B"
    res.loc[
        res["ORDLG_TY_DESC"].isin(["Redemption", "Switch Out"]), "Buy_Sell_Short_Cover"
    ] = "S"
    res.drop(["ORDLG_TY_DESC", "TID.1"], axis=1, inplace=True)

    # Group the trades together
    grouped_result = (
        res.groupby(
            [
                "Fund",
                "TID",
                "TRADE DATE",
                "Buy_Sell_Short_Cover",
                "NAV_NET_VALUE",
                "Name",
                "Trader",
                "Broker",
                "Currency",
            ]
        )
        .sum()
        .reset_index()
    )
    return grouped_result


def fill_information(df):
    # Create standard trade details
    df["OrdStatus"] = "N"
    df["ExecTransType"] = 2
    df["ID_Source"] = "Tid"

    # Create Order and Fill ID
    df.index += 1
    df["ClientOrderID"] = "September " + df["Fund"] + " " + df.index.astype(str)
    df["FillID"] = df["ClientOrderID"]

    # Create Quantitys
    df.rename(columns={"ORDLG_SHARES_VALUE": "Order_Qty"}, inplace=True)
    df["Order_Qty"] = df["Order_Qty"].abs()
    df["Fill_Qty"] = df["Order_Qty"]

    # Create Prices
    df.rename(columns={"NAV_NET_VALUE": "Avg_Price"}, inplace=True)
    df["Fill_Price"] = df["Avg_Price"]

    # Create Dates
    df.rename(columns={"TRADE DATE": "Trade_Date"}, inplace=True)
    df["Settlement_Date"] = df["Trade_Date"]

    # Create Currencies
    df.rename(columns={"Currency": "Security_Currency"}, inplace=True)
    df["Settle_Currency"] = df["Security_Currency"]

    # Create Brokers
    df.rename(columns={"Broker": "Execution_Broker"}, inplace=True)
    df["Clearing_Agent"] = df["Execution_Broker"]

    # Other Renames
    rename_dict = {"TID": "Security_ID", "Name": "Security_Desc"}
    df.rename(columns=rename_dict, inplace=True)

    return df


def create_loader_df():
    loader = pd.DataFrame(
        columns=[
            "OrdStatus",
            "ExecTransType",
            "ClientOrderID",
            "FillID",
            "ID_of_Ord_Fill_Action",
            "Lot_Number",
            "Symbol",
            "Security_Type",
            "Security_Currency",
            "Security_Desc",
            "Buy_Sell_Short_Cover",
            "Open_Close",
            "ID_Source",
            "Security_ID",
            "ISIN",
            "CUSIP",
            "SEDOL",
            "Bloomberg",
            "CINS",
            "When_Issued",
            "Issue_Date",
            "Maturity_Date",
            "Cpn_Repo_Rate",
            "Execution_Int_Days",
            "Accrued_Int",
            "Face_Value",
            "Repo_Type",
            "Repo_Currency",
            "Day_Count_Fract",
            "Repo_Loan_Amt",
            "Trader",
            "Order_Qty",
            "Fill_Qty",
            "Cum_Qty",
            "Hair_Cut",
            "Avg_Price",
            "Fill_Price",
            "Trade_Date",
            "Trade_Time",
            "Execution_Date",
            "Execution_Time",
            "Settlement_Date",
            "Executing_User",
            "Trade_Notes_Commt",
            "Account",
            "Fund",
            "Sub_Fund",
            "Allocation_Code",
            "Strategy_Code",
            "Execution_Broker",
            "Clearing_Agent",
            "Contract_Size",
            "Commission",
            "Spot_FX_Rate",
            "FWD_FX_Points",
            "Fee",
            "Currency_Traded",
            "Settle_Currency",
        ]
    )
    return loader


def create_load_file(loader, trades):
    loader_df = pd.concat([loader, trades], join="outer", axis=0, sort=False)
    loader_df.to_csv("gtl.csv", date_format="%Y%m%d", index=False)


def main():
    g_trades = open_gtrades()
    lookup = open_lookup()
    merged = initial_merge_and_group(g_trades, lookup)
    trades = fill_information(merged)
    loader = create_loader_df()
    create_load_file(loader, trades)


main()
