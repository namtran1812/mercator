import { useEffect } from "react";
import { useMarketStore } from "../store/useMarketStore";
import type { BondPrice } from "../types/bond";

interface StreamingPrice extends BondPrice {
  event_time: string;
  price_change: number;
  source_event_id: string;
  dependency_tenor: string;
  dependency_weight: number;
}

export function usePriceStream() {
  const updateBond = useMarketStore(
    (state) => state.updateBond,
  );

  useEffect(() => {
    const websocket = new WebSocket(
      import.meta.env.VITE_STREAMING_WS,
    );

    websocket.onmessage = (event) => {
      const update = JSON.parse(
        event.data,
      ) as StreamingPrice;

      updateBond(
        update.instrument_id,
        update,
        {
          instrumentId:
            update.instrument_id,
          eventTime:
            update.event_time,
          sourceEventId:
            update.source_event_id,
          dependencyTenor:
            update.dependency_tenor,
          dependencyWeight:
            update.dependency_weight,
          priceChange:
            update.price_change,
        },
      );
    };

    return () => {
      websocket.close();
    };
  }, [updateBond]);
}
