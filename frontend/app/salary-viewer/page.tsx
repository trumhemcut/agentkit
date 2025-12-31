'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Loader2 } from 'lucide-react';
import { A2UIRenderer } from '@/components/A2UI/A2UIRenderer';
import { useA2UIStore } from '@/stores/a2uiStore';
import { sendSalaryViewerMessage, Message as APIMessage } from '@/services/api';
import { v4 as uuidv4 } from 'uuid';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  surfaceId?: string;
  timestamp: number;
}

export default function SalaryViewerPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId] = useState(() => uuidv4());
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const { getSurface, createOrUpdateSurface, updateDataModel, beginRendering } = useA2UIStore();

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: Date.now(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    const runId = uuidv4();
    let assistantMessage: Message = {
      id: uuidv4(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };
    
    setMessages(prev => [...prev, assistantMessage]);

    try {
      const apiMessages: APIMessage[] = messages
        .concat([userMessage])
        .map(msg => ({
          role: msg.role,
          content: msg.content,
        }));

      await sendSalaryViewerMessage(
        apiMessages,
        threadId,
        runId,
        undefined,
        undefined,
        undefined,
        (event) => {
          console.log('[SalaryViewer] Received event:', event);

          switch (event.type) {
            case 'RUN_STARTED':
              console.log('[SalaryViewer] Agent run started');
              break;

            case 'TEXT_MESSAGE_CHUNK':
              // Append text chunks to assistant message
              assistantMessage = {
                ...assistantMessage,
                content: assistantMessage.content + (event.text || ''),
              };
              setMessages(prev => 
                prev.map(msg => msg.id === assistantMessage.id ? assistantMessage : msg)
              );
              break;

            case 'A2UI_BEGIN_RENDER':
              console.log('[SalaryViewer] A2UI render begin:', event);
              const surfaceId = event.surfaceId || `surface-${runId}`;
              createOrUpdateSurface(surfaceId, [], assistantMessage.id);
              
              // Associate surface with message
              assistantMessage = {
                ...assistantMessage,
                surfaceId,
              };
              setMessages(prev => 
                prev.map(msg => msg.id === assistantMessage.id ? assistantMessage : msg)
              );
              break;

            case 'A2UI_UPDATE_DATA_MODEL':
              console.log('[SalaryViewer] A2UI data model update:', event);
              if (event.surfaceId && event.updates) {
                // Convert updates to contents array format
                const contents = Object.entries(event.updates).map(([key, value]) => {
                  if (typeof value === 'string') return { key, valueString: value };
                  if (typeof value === 'number') return { key, valueNumber: value };
                  if (typeof value === 'boolean') return { key, valueBoolean: value };
                  return { key, valueMap: value };
                });
                updateDataModel(event.surfaceId, '/', contents);
              }
              break;

            case 'A2UI_RENDER_COMPONENT':
              console.log('[SalaryViewer] A2UI render component:', event);
              if (event.surfaceId && event.component) {
                createOrUpdateSurface(event.surfaceId, [event.component], assistantMessage.id);
                beginRendering(event.surfaceId, event.component.id);
              }
              break;

            case 'A2UI_FINISH_RENDER':
              console.log('[SalaryViewer] A2UI render finish:', event);
              // Rendering state is already set by beginRendering
              break;

            case 'RUN_FINISHED':
              console.log('[SalaryViewer] Agent run finished');
              setIsLoading(false);
              break;

            case 'ERROR':
              console.error('[SalaryViewer] Error event:', event);
              assistantMessage = {
                ...assistantMessage,
                content: assistantMessage.content + '\n\n❌ Error: ' + (event.message || 'Unknown error'),
              };
              setMessages(prev => 
                prev.map(msg => msg.id === assistantMessage.id ? assistantMessage : msg)
              );
              setIsLoading(false);
              break;

            default:
              console.log('[SalaryViewer] Unhandled event type:', event.type);
          }
        }
      );
    } catch (error) {
      console.error('[SalaryViewer] Error sending message:', error);
      assistantMessage = {
        ...assistantMessage,
        content: '❌ Failed to send message. Please try again.',
      };
      setMessages(prev => 
        prev.map(msg => msg.id === assistantMessage.id ? assistantMessage : msg)
      );
      setIsLoading(false);
    }
  };

  const handleAction = async (actionName: string, context: Record<string, any>) => {
    console.log('[SalaryViewer] User action:', actionName, context);

    if (actionName === 'otp_submit') {
      // User submitted OTP, send it back to the agent
      const otpValue = context.value;
      
      setIsLoading(true);
      
      const userInputMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content: `[Submitted OTP: ${otpValue}]`,
        timestamp: Date.now(),
      };
      
      setMessages(prev => [...prev, userInputMessage]);

      const runId = uuidv4();
      let assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);

      try {
        const apiMessages: APIMessage[] = messages.map(msg => ({
          role: msg.role,
          content: msg.content,
        }));

        await sendSalaryViewerMessage(
          apiMessages,
          threadId,
          runId,
          otpValue,  // Pass user input as OTP
          undefined,
          undefined,
          (event) => {
            console.log('[SalaryViewer] Received event after OTP:', event);

            switch (event.type) {
              case 'TEXT_MESSAGE_CHUNK':
                assistantMessage = {
                  ...assistantMessage,
                  content: assistantMessage.content + (event.text || ''),
                };
                setMessages(prev => 
                  prev.map(msg => msg.id === assistantMessage.id ? assistantMessage : msg)
                );
                break;

              case 'RUN_FINISHED':
                setIsLoading(false);
                break;

              case 'ERROR':
                console.error('[SalaryViewer] Error after OTP:', event);
                assistantMessage = {
                  ...assistantMessage,
                  content: '❌ Error: ' + (event.message || 'Unknown error'),
                };
                setMessages(prev => 
                  prev.map(msg => msg.id === assistantMessage.id ? assistantMessage : msg)
                );
                setIsLoading(false);
                break;
            }
          }
        );
      } catch (error) {
        console.error('[SalaryViewer] Error submitting OTP:', error);
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <CardTitle className="text-2xl">💰 Salary Viewer Agent</CardTitle>
          <CardDescription className="mt-1">
            Ask about salary information - OTP verification required
          </CardDescription>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="container mx-auto max-w-3xl space-y-4">
          {messages.length === 0 && (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <div className="rounded-full bg-primary/10 p-4 mb-4">
                  <Send className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Start a conversation</h3>
                <p className="text-sm text-muted-foreground text-center max-w-md">
                  Try asking: "I'm the CEO, how much did my salary increase this period?"
                </p>
              </CardContent>
            </Card>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <Card className={`max-w-[80%] ${message.role === 'user' ? 'bg-primary text-primary-foreground' : ''}`}>
                <CardContent className="p-4">
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  
                  {/* Render A2UI components if surface exists */}
                  {message.surfaceId && (
                    <div className="mt-4">
                      <A2UIRenderer 
                        surfaceId={message.surfaceId} 
                        onAction={handleAction}
                      />
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <Card className="max-w-[80%]">
                <CardContent className="p-4 flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">Agent is thinking...</span>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t bg-card">
        <div className="container mx-auto max-w-3xl p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex gap-2"
          >
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about salary information..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={!inputValue.trim() || isLoading}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
