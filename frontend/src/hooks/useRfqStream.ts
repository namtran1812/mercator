import { useEffect } from "react";
import {
  useQueryClient,
} from "@tanstack/react-query";

interface RfqQuotedEvent {
  event_type: "RFQ_QUOTED";
  rfq_id: string;
}

interface TradeExecutedEvent {
  event_type: "TRADE_EXECUTED";
  rfq_id: string;
}

type RfqStreamEvent =
  | RfqQuotedEvent
  | TradeExecutedEvent;

export function useRfqStream(
  rfqId: string | null,
) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!rfqId) {
      return;
    }

    const websocket = new WebSocket(
      `${import.meta.env.VITE_RFQ_WS}/${rfqId}`,
    );

    websocket.onmessage = async (
      event,
    ) => {
      const payload = JSON.parse(
        event.data,
      ) as RfqStreamEvent;

      await queryClient.invalidateQueries({
        queryKey: [
          "rfq-detail",
          rfqId,
        ],
      });

      if (
        payload.event_type
        === "TRADE_EXECUTED"
      ) {
        await queryClient.invalidateQueries({
          queryKey: [
            "live-account-risk",
          ],
        });
      }
    };

    websocket.onerror = () => {
      console.error(
        "RFQ stream disconnected",
      );
    };

    return () => {
      websocket.close();
    };
  }, [queryClient, rfqId]);
}
