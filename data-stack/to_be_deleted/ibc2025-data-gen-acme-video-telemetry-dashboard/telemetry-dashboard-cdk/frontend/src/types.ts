export interface TelemetryEvent {
  eventId: string;
  timestamp: string;
  customerId: string;
  deviceId: string;
  sessionId: string;
  eventType: 'start' | 'stop' | 'pause' | 'resume' | 'buffering' | 'error' | 'quality_change' | 'complete';
  contentId: string;
  contentTitle?: string;
  streamQuality: 'SD' | 'HD' | 'FHD' | '4K';
  deviceType: 'mobile' | 'tablet' | 'desktop' | 'tv' | 'game_console';
  deviceModel?: string;
  osName?: string;
  osVersion?: string;
  appVersion?: string;
  country?: string;
  region?: string;
  city?: string;
  isp?: string;
  connectionType?: string;
  buffering?: {
    duration: number;
    count: number;
  };
  error?: {
    code: string;
    message: string;
  };
  qualityMetrics?: {
    bitrate: number;
    fps: number;
    droppedFrames: number;
    resolution: string;
  };
  duration?: number;
  position?: number;
}