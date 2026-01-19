import React from 'react';
import { format } from 'date-fns';
import { TelemetryEvent } from '../types';
import './EventFeed.css';

interface EventFeedProps {
  events: TelemetryEvent[];
}

const EventFeed: React.FC<EventFeedProps> = ({ events }) => {
  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'start': return '▶️';
      case 'stop': return '⏹️';
      case 'pause': return '⏸️';
      case 'resume': return '⏯️';
      case 'buffering': return '⏳';
      case 'error': return '⚠️';
      case 'quality_change': return '📊';
      case 'complete': return '✅';
      default: return '📺';
    }
  };

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'start': return '#4ade80';
      case 'stop': return '#f87171';
      case 'pause': return '#fbbf24';
      case 'resume': return '#60a5fa';
      case 'buffering': return '#fb923c';
      case 'error': return '#ef4444';
      case 'quality_change': return '#a78bfa';
      case 'complete': return '#34d399';
      default: return '#94a3b8';
    }
  };

  const getQualityBadgeColor = (quality: string) => {
    switch (quality) {
      case '4K': return '#ef4444';
      case 'FHD': return '#f59e0b';
      case 'HD': return '#3b82f6';
      case 'SD': return '#6b7280';
      default: return '#94a3b8';
    }
  };

  return (
    <div className="event-feed">
      <div className="feed-header">
        <h2>📡 Live Event Stream</h2>
        <span className="event-count">{events.length} events</span>
      </div>
      
      <div className="events-container">
        {events.length === 0 ? (
          <div className="no-events">
            <p>Waiting for telemetry events...</p>
          </div>
        ) : (
          events.map((event) => (
            <div key={event.eventId} className="event-card">
              <div className="event-header">
                <div className="event-type" style={{ color: getEventColor(event.eventType) }}>
                  <span className="event-icon">{getEventIcon(event.eventType)}</span>
                  <span className="event-type-text">{event.eventType.toUpperCase()}</span>
                </div>
                <div className="event-timestamp">
                  {format(new Date(event.timestamp), 'HH:mm:ss.SSS')}
                </div>
              </div>
              
              <div className="event-content">
                <div className="event-main-info">
                  <div className="content-info">
                    <span className="content-title">{event.contentTitle || event.contentId}</span>
                    <span className="quality-badge" style={{ backgroundColor: getQualityBadgeColor(event.streamQuality) }}>
                      {event.streamQuality}
                    </span>
                  </div>
                  
                  <div className="event-details">
                    <div className="detail-item">
                      <span className="detail-label">Customer:</span>
                      <span className="detail-value">{event.customerId}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Device:</span>
                      <span className="detail-value">{event.deviceType}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Location:</span>
                      <span className="detail-value">{event.city}, {event.country}</span>
                    </div>
                  </div>
                </div>
                
                {event.qualityMetrics && (
                  <div className="metrics-row">
                    <span className="metric">
                      📊 {event.qualityMetrics.bitrate} kbps
                    </span>
                    <span className="metric">
                      🎬 {event.qualityMetrics.fps} fps
                    </span>
                    <span className="metric">
                      📐 {event.qualityMetrics.resolution}
                    </span>
                  </div>
                )}
                
                {event.buffering && (
                  <div className="buffering-info">
                    ⏳ Buffering: {event.buffering.duration}ms ({event.buffering.count} times)
                  </div>
                )}
                
                {event.error && (
                  <div className="error-info">
                    ⚠️ Error: {event.error.message} (Code: {event.error.code})
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default EventFeed;