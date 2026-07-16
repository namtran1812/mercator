import { useMemo } from "react";
import {
  AllCommunityModule,
  ModuleRegistry,
  type ColDef,
} from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useMarketStore } from "../../store/useMarketStore";
import type { BondPrice } from "../../types/bond";

ModuleRegistry.registerModules([AllCommunityModule]);

export function BondGrid() {
  const bonds = useMarketStore((state) => state.bonds);
  const selectBond = useMarketStore((state) => state.selectBond);

  const columns = useMemo<ColDef<BondPrice>[]>(
    () => [
      {
        field: "instrument_id",
        headerName: "ID",
        width: 90,
      },
      {
        field: "clean_price",
        headerName: "Price",
        valueFormatter: ({ value }) =>
          typeof value === "number" ? value.toFixed(2) : "",
      },
      {
        field: "yield_to_maturity",
        headerName: "Yield",
        valueFormatter: ({ value }) =>
          typeof value === "number"
            ? `${(value * 100).toFixed(2)}%`
            : "",
      },
      {
        field: "g_spread_bps",
        headerName: "G-Spread",
        valueFormatter: ({ value }) =>
          typeof value === "number"
            ? `${value.toFixed(1)} bp`
            : "",
      },
      {
        field: "modified_duration",
        headerName: "Duration",
        valueFormatter: ({ value }) =>
          typeof value === "number" ? value.toFixed(2) : "",
      },
      {
        field: "quality_status",
        headerName: "Quality",
      },
    ],
    [],
  );

  return (
    <div className="bond-grid">
      <AgGridReact<BondPrice>
        rowData={bonds}
        columnDefs={columns}
        rowSelection="single"
        onRowClicked={(event) => {
          if (event.data) {
            selectBond(event.data.instrument_id);
          }
        }}
        defaultColDef={{
          sortable: true,
          resizable: true,
          flex: 1,
          minWidth: 110,
        }}
      />
    </div>
  );
}
