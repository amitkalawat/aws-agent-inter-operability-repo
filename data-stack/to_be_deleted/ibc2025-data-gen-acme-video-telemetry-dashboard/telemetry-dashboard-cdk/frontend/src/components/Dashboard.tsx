import React, { useState, useEffect, useRef } from 'react';
import { Auth } from 'aws-amplify';
import EventFeed from './EventFeed';
import { TelemetryEvent } from '../types';
import { config } from '../config';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [debugLogs, setDebugLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Debug logging function
  const addDebugLog = (message: string) => {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log(logMessage);
    setDebugLogs(prev => [...prev.slice(-49), logMessage]); // Keep last 50 logs
  };

  const connectWebSocket = async () => {
    try {
      addDebugLog('Starting WebSocket connection...');
      addDebugLog(`WebSocket URL: ${config.webSocketUrl}`);
      
      // Get the current auth session and ID token
      const session = await Auth.currentSession();
      const token = session.getIdToken().getJwtToken();
      
      if (!token) {
        addDebugLog('ERROR: No auth token available');
        setConnectionError('Authentication required');
        return;
      }
      
      addDebugLog(`Token obtained, length: ${token.length}`);
      const wsUrl = `${config.webSocketUrl}?token=${token}`;
      addDebugLog(`Connecting to WebSocket...`);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        addDebugLog('WebSocket connected successfully');
        setIsConnected(true);
        setConnectionError(null);
      };

      ws.onmessage = (event) => {
        try {
          addDebugLog(`WebSocket message received, size: ${event.data.length} bytes`);
          const data = JSON.parse(event.data);
          addDebugLog(`Parsed message: action=${data.action}, has events=${!!data.events}, event count=${data.events?.length || 0}`);
          
          if (data.action === 'telemetry' && data.events && Array.isArray(data.events)) {
            // Process and transform events from MSK
            const rawEvents = data.events;
            addDebugLog(`Processing ${rawEvents.length} telemetry events`);
            
            // Map backend property names to frontend property names
            const newEvents: TelemetryEvent[] = rawEvents.map((rawEvent: any) => ({
              eventId: rawEvent.event_id,
              timestamp: rawEvent.event_timestamp || rawEvent.timestamp,
              customerId: rawEvent.customer_id,
              deviceId: rawEvent.device_id,
              sessionId: rawEvent.session_id,
              eventType: rawEvent.event_type,
              contentId: rawEvent.title_id || rawEvent.content_id,
              contentTitle: rawEvent.title_name || rawEvent.content_title,
              streamQuality: rawEvent.quality || 'HD',
              deviceType: rawEvent.device_type || 'unknown',
              deviceModel: rawEvent.device_model,
              osName: rawEvent.device_os,
              osVersion: rawEvent.os_version,
              appVersion: rawEvent.app_version,
              country: rawEvent.country,
              region: rawEvent.state || rawEvent.region,
              city: rawEvent.city,
              isp: rawEvent.isp,
              connectionType: rawEvent.connection_type,
              buffering: rawEvent.buffering_events > 0 ? {
                duration: rawEvent.buffering_duration_seconds * 1000,
                count: rawEvent.buffering_events
              } : undefined,
              error: rawEvent.error_count > 0 ? {
                code: 'ERROR',
                message: `${rawEvent.error_count} errors occurred`
              } : undefined,
              qualityMetrics: {
                bitrate: Math.round(rawEvent.bandwidth_mbps * 1000), // Convert to kbps
                fps: 30, // Default FPS
                droppedFrames: 0,
                resolution: rawEvent.quality === '4K' ? '3840x2160' : 
                           rawEvent.quality === 'HD' ? '1920x1080' : '1280x720'
              },
              duration: rawEvent.watch_duration_seconds,
              position: rawEvent.position_seconds
            }));
            
            if (newEvents.length > 0) {
              // Log first event details
              const firstEvent = newEvents[0];
              addDebugLog(`First event mapped: type=${firstEvent.eventType}, customer=${firstEvent.customerId}, device=${firstEvent.deviceType}`);
              
              setEvents(prev => {
                const updated = [...newEvents, ...prev].slice(0, 100);
                addDebugLog(`Total events in state: ${updated.length}`);
                return updated;
              });
              
            }
          } else {
            addDebugLog(`Non-telemetry message received: ${JSON.stringify(data)}`);
          }
        } catch (error) {
          addDebugLog(`ERROR parsing WebSocket message: ${error}`);
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        addDebugLog(`WebSocket error: ${error}`);
        console.error('WebSocket error:', error);
        setConnectionError('Connection error occurred');
      };

      ws.onclose = (event) => {
        addDebugLog(`WebSocket disconnected: code=${event.code}, reason=${event.reason}`);
        setIsConnected(false);
        
        // Attempt to reconnect after 5 seconds
        addDebugLog('Will attempt to reconnect in 5 seconds...');
        reconnectTimeoutRef.current = setTimeout(() => {
          addDebugLog('Attempting to reconnect...');
          connectWebSocket();
        }, 5000);
      };

      wsRef.current = ws;
    } catch (error) {
      addDebugLog(`Failed to connect WebSocket: ${error}`);
      console.error('Failed to connect WebSocket:', error);
      setConnectionError('Failed to establish connection');
    }
  };


  useEffect(() => {
    addDebugLog('Dashboard component mounted');
    addDebugLog(`Config: ${JSON.stringify(config)}`);
    connectWebSocket();

    return () => {
      addDebugLog('Dashboard component unmounting');
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);


  return (
    <div className="dashboard">
      <div className="connection-status">
        <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
        {connectionError && (
          <div className="connection-error">{connectionError}</div>
        )}
      </div>

      
      <div className="dashboard-content">
        <EventFeed events={events} />
      </div>
      
      {/* Debug console */}
      <div style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        maxHeight: '200px',
        overflowY: 'auto',
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        color: '#00ff00',
        fontSize: '10px',
        fontFamily: 'monospace',
        padding: '10px',
        borderTop: '2px solid #00ff00'
      }}>
        <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>Debug Console (Events: {events.length})</div>
        {debugLogs.map((log, index) => (
          <div key={index}>{log}</div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;