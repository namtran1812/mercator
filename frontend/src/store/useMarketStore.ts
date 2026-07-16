import { create } from "zustand";
import type { BondPrice } from "../types/bond";

interface MarketState {
  bonds: BondPrice[];
  selectedBondId: number | null;

  setBonds: (bonds: BondPrice[]) => void;

  updateBond: (
    instrumentId: number,
    update: Partial<BondPrice>,
  ) => void;

  selectBond: (
    instrumentId: number,
  ) => void;
}

export const useMarketStore =
  create<MarketState>((set) => ({
    bonds: [],
    selectedBondId: null,

    setBonds: (bonds) =>
      set({ bonds }),

    updateBond: (
      instrumentId,
      update,
    ) =>
      set((state) => ({
        bonds: state.bonds.map((bond) =>
          bond.instrument_id === instrumentId
            ? {
                ...bond,
                ...update,
              }
            : bond,
        ),
      })),

    selectBond: (instrumentId) =>
      set({
        selectedBondId: instrumentId,
      }),
  }));
