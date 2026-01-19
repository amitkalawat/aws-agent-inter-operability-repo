import React, { useState, useEffect, useRef } from 'react';
import { User } from '../services/AuthService';
import AgentCoreService, { ChatMessage } from '../services/AgentCoreService';

interface ChatInterfaceProps {
  user: User;
}

interface ImageWithLoaderProps {
  src: string;
  alt: string;
  className?: string;
  onError: (e: React.SyntheticEvent<HTMLImageElement>) => void;
}

const ImageWithLoader: React.FC<ImageWithLoaderProps> = ({ src, alt, className, onError }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    setIsLoading(false);
    setHasError(true);
    onError(e);
  };

  return (
    <>
      {isLoading && !hasError && (
        <div className="chart-loading-container">
          <div className="chart-skeleton">
            <div className="skeleton-bar skeleton-bar-1"></div>
            <div className="skeleton-bar skeleton-bar-2"></div>
            <div className="skeleton-bar skeleton-bar-3"></div>
            <div className="skeleton-bar skeleton-bar-4"></div>
          </div>
          <p className="loading-text">Loading chart...</p>
        </div>
      )}
      <img 
        src={src}
        alt={alt}
        className={`${className || ''} ${isLoading ? 'image-loading' : 'image-loaded'}`}
        onLoad={handleLoad}
        onError={handleError}
        style={{ 
          display: isLoading || hasError ? 'none' : 'block',
          opacity: isLoading ? 0 : 1,
          transition: 'opacity 0.3s ease-in-out'
        }}
      />
    </>
  );
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ user }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'testing' | 'connected' | 'error' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streamingEnabled, setStreamingEnabled] = useState(true);
  const [currentStreamingMessageId, setCurrentStreamingMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Test connection to AgentCore when component mounts
    testConnection();
    // Add welcome message
    addSystemMessage('Welcome! I\'m your AI assistant powered by Amazon Bedrock AgentCore. How can I help you today?');
  }, []);

  useEffect(() => {
    // Scroll to bottom when new messages are added
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const testConnection = async () => {
    setConnectionStatus('testing');
    try {
      const result = await AgentCoreService.testConnection(user.accessToken);
      if (result.success) {
        setConnectionStatus('connected');
        setError(null);
      } else {
        setConnectionStatus('error');
        setError(result.message);
      }
    } catch (error: any) {
      setConnectionStatus('error');
      setError(error.message || 'Failed to test connection');
    }
  };

  const addSystemMessage = (content: string) => {
    const systemMessage: ChatMessage = {
      id: `system-${Date.now()}`,
      role: 'assistant',
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, systemMessage]);
  };

  const addUserMessage = (content: string): ChatMessage => {
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    return userMessage;
  };

  const addAssistantMessage = (content: string, isError: boolean = false): ChatMessage => {
    const assistantMessage: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: isError ? `❌ Error: ${content}` : content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, assistantMessage]);
    return assistantMessage;
  };

  const addStreamingMessage = (): ChatMessage => {
    const streamingMessage: ChatMessage = {
      id: `streaming-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, streamingMessage]);
    setCurrentStreamingMessageId(streamingMessage.id);
    return streamingMessage;
  };

  const updateStreamingMessage = (messageId: string, newContent: string) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, content: newContent }
        : msg
    ));
  };

  const completeStreamingMessage = () => {
    setCurrentStreamingMessageId(null);
    setIsStreaming(false);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || isStreaming) return;
    
    const messageText = inputMessage.trim();
    setInputMessage('');
    setError(null);

    // Add user message
    addUserMessage(messageText);

    if (streamingEnabled) {
      // Handle streaming response
      setIsStreaming(true);
      const streamingMessage = addStreamingMessage();
      let accumulatedContent = '';

      try {
        await AgentCoreService.sendStreamingMessage(messageText, user.accessToken, {
          onChunk: (chunk: string) => {
            accumulatedContent += chunk;
            updateStreamingMessage(streamingMessage.id, accumulatedContent);
          },
          onComplete: (fullResponse: string) => {
            updateStreamingMessage(streamingMessage.id, fullResponse);
            completeStreamingMessage();
          },
          onError: (error: string) => {
            updateStreamingMessage(streamingMessage.id, `❌ Error: ${error}`);
            setError(error);
            completeStreamingMessage();
          }
        });
      } catch (error: any) {
        const errorMessage = error.message || 'Failed to send streaming message';
        updateStreamingMessage(streamingMessage.id, `❌ Error: ${errorMessage}`);
        setError(errorMessage);
        completeStreamingMessage();
      }
    } else {
      // Handle regular response
      setIsLoading(true);
      try {
        const response = await AgentCoreService.sendMessage(messageText, user.accessToken);
        
        if (response.status === 'success') {
          addAssistantMessage(response.response);
        } else {
          addAssistantMessage(response.error || 'Failed to get response from AgentCore', true);
          setError(response.error || 'Unknown error');
        }
      } catch (error: any) {
        const errorMessage = error.message || 'Failed to send message';
        addAssistantMessage(errorMessage, true);
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewConversation = () => {
    AgentCoreService.resetSession();
    setMessages([]);
    addSystemMessage('New conversation started! How can I help you?');
    setError(null);
  };

  const handleAWSDocumentationQuery = async (query: string) => {
    if (isLoading) return;
    
    setInputMessage(query);
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };

  const awsDocumentationSuggestions = [
    {
      title: "AWS Lambda Functions",
      query: "Search AWS documentation for Lambda function configuration and best practices"
    },
    {
      title: "S3 Bucket Policies", 
      query: "Find AWS documentation about S3 bucket policies and security"
    },
    {
      title: "EC2 Instance Types",
      query: "Search AWS documentation for EC2 instance types and pricing"
    },
    {
      title: "RDS Database Setup",
      query: "Find AWS documentation about setting up RDS databases"
    },
    {
      title: "VPC Networking",
      query: "Search AWS documentation for VPC networking and security groups"
    },
    {
      title: "IAM Permissions",
      query: "Find AWS documentation about IAM roles and policies"
    }
  ];

  // Function to detect and extract image URLs from text
  const detectImageUrls = (text: string): string[] => {
    const imageUrls: string[] = [];
    
    // S3 presigned URLs
    const s3Pattern = /https:\/\/[^\s]+\.s3\.[^\s]+\.amazonaws\.com\/[^\s]+/g;
    const s3Matches = text.match(s3Pattern);
    if (s3Matches) {
      const validS3Images = s3Matches.filter(url => 
        url.includes('.png') || url.includes('.jpg') || url.includes('.jpeg') || 
        url.includes('chart') || url.includes('visualization')
      );
      imageUrls.push(...validS3Images);
    }
    
    // CloudFront URLs
    const cloudfrontPattern = /https:\/\/[a-zA-Z0-9.-]+\.cloudfront\.net\/[^\s\[\]"]+/g;
    const cfMatches = text.match(cloudfrontPattern);
    if (cfMatches) {
      const validCfImages = cfMatches.filter(url =>
        url.includes('.png') || url.includes('.jpg') || url.includes('.jpeg') ||
        url.includes('.webp') || url.includes('.gif')
      );
      imageUrls.push(...validCfImages);
    }
    
    return imageUrls;
  };

  const formatMessage = (content: string) => {
    // First check for plain image URLs not in markdown format
    const detectedImageUrls = detectImageUrls(content);
    
    // Parse content for markdown images and S3 URLs
    const lines = content.split('\n');
    
    const formattedLines = lines.map((line, lineIndex) => {
      // Check for markdown image syntax: ![alt text](url)
      const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
      const parts: (string | React.ReactElement)[] = [];
      let lastIndex = 0;
      let match;

      while ((match = imageRegex.exec(line)) !== null) {
        // Add text before the image
        if (match.index > lastIndex) {
          parts.push(line.substring(lastIndex, match.index));
        }

        const altText = match[1];
        const imageUrl = match[2];
        
        // Check if it's an S3 URL or CloudFront URL with image extension or contains chart visualization
        const isS3ImageUrl = imageUrl.includes('s3.amazonaws.com') && 
                            (imageUrl.includes('.png') || imageUrl.includes('.jpg') || imageUrl.includes('.jpeg') || 
                             imageUrl.includes('chart') || imageUrl.includes('visualization'));
        
        const isCloudFrontImageUrl = imageUrl.includes('cloudfront.net') && 
                                   (imageUrl.includes('.png') || imageUrl.includes('.jpg') || imageUrl.includes('.jpeg') ||
                                    imageUrl.includes('.webp') || imageUrl.includes('.gif'));
        
        const isImageUrl = isS3ImageUrl || isCloudFrontImageUrl;
        
        if (isImageUrl) {
          parts.push(
            <div key={`image-${lineIndex}-${match.index}`} className="message-image-container">
              <ImageWithLoader
                src={imageUrl}
                alt={altText || 'Chart visualization'}
                className="message-image"
                onError={(e) => {
                  // Fallback to link if image fails to load
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                  const link = document.createElement('a');
                  link.href = imageUrl;
                  link.textContent = altText || imageUrl;
                  link.target = '_blank';
                  link.className = 'image-fallback-link';
                  target.parentNode?.appendChild(link);
                }}
              />
              <p className="image-caption">{altText}</p>
            </div>
          );
        } else {
          // Not an image URL, render as regular link
          parts.push(
            <a key={`link-${lineIndex}-${match.index}`} href={imageUrl} target="_blank" rel="noopener noreferrer">
              {altText || imageUrl}
            </a>
          );
        }

        lastIndex = imageRegex.lastIndex;
      }

      // Add any remaining text after the last image (only if it's not empty/whitespace)
      const remainingText = line.substring(lastIndex).trim();
      if (remainingText && parts.length === 0) {
        // Only add remaining text if no images were processed on this line
        parts.push(line);
      } else if (remainingText && parts.length > 0) {
        // Only add meaningful remaining text if there are images
        parts.push(remainingText);
      }

      // If no images were found and no meaningful text, just return the line as text
      if (parts.length === 0) {
        parts.push(line);
      }

      return (
        <span key={lineIndex}>
          {parts}
          {lineIndex < lines.length - 1 && <br />}
        </span>
      );
    });
    
    // Add detected plain image URLs as gallery at the end
    if (detectedImageUrls.length > 0) {
      const imageGallery = (
        <div key="image-gallery" className="message-image-gallery">
          {detectedImageUrls.map((url, index) => {
            // Remove URL from the content to avoid duplication
            const cleanedUrl = url.split('?')[0]; // Remove query parameters for display
            return (
              <div key={`gallery-image-${index}`} className="message-image-container">
                <ImageWithLoader
                  src={url}
                  alt={`Generated image ${index + 1}`}
                  className="message-image"
                  onError={(e) => {
                    console.error('Failed to load image:', url);
                    e.currentTarget.style.display = 'none';
                  }}
                />
                <p className="image-caption">Generated image {index + 1}</p>
              </div>
            );
          })}
        </div>
      );
      
      return (
        <div>
          {formattedLines}
          {imageGallery}
        </div>
      );
    }
    
    return formattedLines;
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="chat-container">
      {/* Connection Status */}
      <div className="connection-status">
        {connectionStatus === 'testing' && (
          <div className="status-indicator testing">
            <div className="spinner"></div>
            Testing connection to AgentCore...
          </div>
        )}
        {connectionStatus === 'connected' && (
          <div className="status-indicator connected">
            🟢 Connected to AgentCore
            <label className="streaming-toggle">
              <input
                type="checkbox"
                checked={streamingEnabled}
                onChange={(e) => setStreamingEnabled(e.target.checked)}
              />
              ⚡ Streaming {streamingEnabled ? 'ON' : 'OFF'}
            </label>
            <button className="new-chat-button" onClick={handleNewConversation}>
              🆕 New Chat
            </button>
          </div>
        )}
        {connectionStatus === 'error' && (
          <div className="status-indicator error">
            🔴 Connection Error
            <button className="retry-button" onClick={testConnection}>
              🔄 Retry
            </button>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          ⚠️ {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Messages */}
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-header">
              <span className="message-sender">
                {message.role === 'user' ? '👤 You' : '🤖 Assistant'}
              </span>
              <span className="message-time">
                {formatTime(message.timestamp)}
              </span>
            </div>
            <div className="message-content">
              {formatMessage(message.content)}
              {currentStreamingMessageId === message.id && isStreaming && (
                <span className="terminal-cursor">█</span>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && !streamingEnabled && (
          <div className="message assistant">
            <div className="message-header">
              <span className="message-sender">🤖 Assistant</span>
              <span className="message-time">typing...</span>
            </div>
            <div className="message-content typing-indicator">
              <div className="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              Processing your request...
            </div>
          </div>
        )}
        
        {isStreaming && currentStreamingMessageId && !messages.find(m => m.id === currentStreamingMessageId)?.content && (
          <div className="message assistant streaming">
            <div className="message-header">
              <span className="message-sender">🤖 Assistant</span>
              <span className="message-time">⚡ streaming...</span>
            </div>
            <div className="message-content">
              <span className="terminal-cursor">█</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              connectionStatus === 'connected' 
                ? "Type your message... (Press Enter to send, Shift+Enter for new line)"
                : "Connecting to AgentCore..."
            }
            disabled={isLoading || isStreaming || connectionStatus !== 'connected'}
            rows={1}
            className="message-input"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading || isStreaming || connectionStatus !== 'connected'}
            className="send-button"
            title="Send message"
          >
            {isLoading ? '⏳' : isStreaming ? '⚡' : '📤'}
          </button>
        </div>
        
      </div>
    </div>
  );
};

export default ChatInterface;