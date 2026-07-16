import { create } from "zustand";
import type { BondPrice } from "../types/bond";

export interface StreamMetadata {
  instrumentId: number;
  eventTime: string;
  sourceEventId: string;
  dependencyTenor: string;
  dependencyWeight: number;
  priceChange: number;
}

interface MarketState {
  bonds: BondPrice[];
  selectedBondId: number | null;
  lastStreamUpdate: StreamMetadata | null;

  setBonds: (bonds: BondPrice[]) => void;

  updateBond: (
    instrumentId: number,
    update: Partial<BondPrice>,
    metadata?: StreamMetadata,
  ) => void;

  selectBond: (
    instrumentId: number,
  ) => void;
}

export const useMarketStore =
  create<MarketState>((set) => ({
    bonds: [],
    selectedBondId: null,
    lastStreamUpdate: null,

    setBonds: (bonds) =>
      set({ bonds }),

    updateBond: (
      instrumentId,
      update,
      metadata,
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

        lastStreamUpdate:
          metadata ??
          state.lastStreamUpdate,
      })),

    selectBond: (instrumentId) =>
      set({
        selectedBondId: instrumentId,
      }),
  }));
