// hooks/useOnboardingAgent.ts
import { useState, useCallback } from 'react';

export interface UICommand {
  action: 'navigate' | 'update' | 'validate' | 'show_error' | 'update_ui_settings';
  component: string;
  props: Record<string, any>;
}

export interface OnboardingState {
  current_step: number;
  step_name: string;
  progress: number;
  is_complete: boolean;
}

export interface AgentResponse {
  text: string;
  ui_commands: UICommand[];
  onboarding_state: OnboardingState;
}

export interface UseOnboardingAgentReturn {
  sendAction: (action: string, data?: Record<string, any>) => Promise<AgentResponse>;
  isLoading: boolean;
  error: string | null;
}

export const useOnboardingAgent = (agentUrl: string = 'http://localhost:8082'): UseOnboardingAgentReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendAction = useCallback(async (
    action: string,
    data: Record<string, any> = {}
  ): Promise<AgentResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        action,
        data,
        timestamp: new Date().toISOString()
      };

      // Use A2A JSONRPC protocol with required fields
      const jsonrpcRequest = {
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'message/send',
        params: {
          message: {
            messageId: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'user',
            parts: [{
              text: JSON.stringify(payload)
            }]
          }
        }
      };

      const response = await fetch(agentUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jsonrpcRequest),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // Handle JSONRPC response
      if (result.error) {
        throw new Error(result.error.message || 'Agent error');
      }

      // Parse the agent's response from JSONRPC result
      const artifactText = result.result?.artifacts?.[0]?.parts?.[0]?.text;
      if (!artifactText) {
        throw new Error('Invalid response format from agent');
      }

      const agentResponse: AgentResponse = JSON.parse(artifactText);
      return agentResponse;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [agentUrl]);

  return { sendAction, isLoading, error };
};
