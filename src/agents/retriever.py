from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd
from ..types import InvoiceLine, POLine, ReceiptLine, Evidence


def retrieve_local(invoice_id: str, dfs: Dict[str, pd.DataFrame]) -> Evidence:
    inv_df = dfs["invoices"]
    po_df = dfs["pos"]
    gr_df = dfs["receipts"]

    inv_rows = inv_df[inv_df["invoice_id"].str.upper() == invoice_id]
    if inv_rows.empty:
        return Evidence(invoice_lines=[], po_lines=[], receipts=[], web_results=[], source_offsets={})

    po_numbers = inv_rows["po_number"].dropna().unique().tolist()
    po_rows = po_df[po_df["po_number"].isin(po_numbers)] if po_numbers else po_df.iloc[0:0]
    gr_rows = gr_df[gr_df["po_number"].isin(po_numbers)] if po_numbers else gr_df.iloc[0:0]

    invoice_lines: List[InvoiceLine] = [InvoiceLine(**r.to_dict()) for _, r in inv_rows.iterrows()]
    po_lines: List[POLine] = [POLine(**r.to_dict()) for _, r in po_rows.iterrows()]
    receipts: List[ReceiptLine] = [ReceiptLine(**r.to_dict()) for _, r in gr_rows.iterrows()]

    source_offsets = {
        "invoices.csv": inv_rows.index.astype(int).tolist(),
        "pos.csv": po_rows.index.astype(int).tolist(),
        "receipts.csv": gr_rows.index.astype(int).tolist(),
    }

    return Evidence(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        receipts=receipts,
        web_results=[],
        source_offsets=source_offsets,
    )


def attach_web_results(evidence: Evidence, web_results: List[Dict[str, Any]]) -> Evidence:
    evidence.web_results = web_results
    return evidence