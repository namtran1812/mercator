import { create } from "zustand";
import type { BondPrice } from "../types/bond";

interface MarketState {
  bonds: BondPrice[];
  selectedBondId: number | null;
  setBonds: (bonds: BondPrice[]) => void;
  selectBond: (instrumentId: number) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  bonds: [],
  selectedBondId: null,
  setBonds: (bonds) => set({ bonds }),
  selectBond: (instrumentId) =>
    set({ selectedBondId: instrumentId }),
}));
