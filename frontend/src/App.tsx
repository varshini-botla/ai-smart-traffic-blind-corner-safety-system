import React, { useEffect, useState } from "react";
import { UnifiedSystemPage } from "./pages/UnifiedSystemPage";
import { checkHealth, WS_URL } from "./services/api";

export const App: React.FC = () => {
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(true);
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);

  // Health checking polling
  const verifyHealth = async () => {
    try {
      await checkHealth();
      setIsBackendOnline(true);
    } catch {
      setIsBackendOnline(false);
    }
  };

  useEffect(() => {
    verifyHealth();
    const interval = setInterval(verifyHealth, 10000);

    // WebSocket connection
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => setIsWsConnected(true);
      ws.onclose = () => setIsWsConnected(false);
      ws.onerror = () => setIsWsConnected(false);
    } catch {
      setIsWsConnected(false);
    }

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, []);

  return (
    <UnifiedSystemPage
      isBackendOnline={isBackendOnline}
      isWsConnected={isWsConnected}
    />
  );
};
