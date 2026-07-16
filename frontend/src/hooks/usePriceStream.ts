import { useEffect } from "react";
import { useMarketStore } from "../store/useMarketStore";
import type { BondPrice } from "../types/bond";

interface StreamingPrice extends BondPrice {
  event_time: string;
  price_change: number;
  source_event_id: string;
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
      );
    };

    websocket.onerror = () => {
      console.error(
        "Mercator price stream disconnected",
      );
    };

    return () => {
      websocket.close();
    };
  }, [updateBond]);
}
