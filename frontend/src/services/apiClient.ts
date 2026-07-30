/**
 * Frontend HTTP REST API Client Service for Traffic Simulation Framework.
 * Deliverable: ISSUE-041 (Frontend API Client Service)
 * 
 * Provides typed wrappers for configuration validation, simulation creation,
 * lifecycle control actions, and final metrics report fetching.
 */

import type {
  ScenarioConfig,
  ValidationResult,
  CreateSimulationResponse,
  SimulationStatusResponse,
  ControlAction,
  ControlActionResponse,
  FinalMetricsResponse,
  HealthCheckResponse,
  ApiErrorDetail,
  ApiErrorResponse,
  ErrorNotificationHook,
} from '../types/api';

export class ApiClientError extends Error {
  public readonly code: string;
  public readonly httpStatus: number;
  public readonly details?: unknown;
  public readonly timestamp?: string;

  constructor(code: string, message: string, httpStatus = 500, details?: unknown, timestamp?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.httpStatus = httpStatus;
    this.details = details;
    this.timestamp = timestamp || new Date().toISOString();
  }
}

export class ApiClient {
  private baseUrl: string;
  private errorHooks: Set<ErrorNotificationHook> = new Set();

  constructor(baseUrl?: string) {
    const defaultUrl =
      typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL
        ? import.meta.env.VITE_API_BASE_URL
        : 'http://localhost:8000/api/v1';
    this.baseUrl = (baseUrl || defaultUrl).replace(/\/+$/, '');
  }

  /**
   * Set or update the base API URL.
   */
  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  /**
   * Get the current base API URL.
   */
  public getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Register a user-facing notification hook to receive API error alerts.
   * Returns an unsubscribe callback function.
   */
  public registerErrorHook(hook: ErrorNotificationHook): () => void {
    this.errorHooks.add(hook);
    return () => this.errorHooks.delete(hook);
  }

  /**
   * Unregister an error notification hook.
   */
  public removeErrorHook(hook: ErrorNotificationHook): void {
    this.errorHooks.delete(hook);
  }

  /**
   * Notify all registered error notification hooks.
   */
  private notifyErrorHooks(errorDetail: ApiErrorDetail, httpStatus?: number): void {
    this.errorHooks.forEach((hook) => {
      try {
        hook(errorDetail, httpStatus);
      } catch (err) {
        console.error('Error in user-facing error notification hook:', err);
      }
    });
  }

  /**
   * Internal helper to execute HTTP requests with error handling and notification logging.
   */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, { ...options, headers });

      if (!response.ok) {
        let errorDetail: ApiErrorDetail;

        try {
          const body = (await response.json()) as ApiErrorResponse | Record<string, unknown>;
          if ('error' in body && typeof body.error === 'object' && body.error !== null) {
            errorDetail = body.error as ApiErrorDetail;
          } else {
            const fallbackMessage =
              typeof body === 'object' && body !== null && 'message' in body && typeof body.message === 'string'
                ? body.message
                : response.statusText || 'An unexpected API error occurred';

            errorDetail = {
              code: `HTTP_${response.status}`,
              message: fallbackMessage,
              details: body,
              timestamp: new Date().toISOString(),
            };
          }
        } catch {
          errorDetail = {
            code: `HTTP_${response.status}`,
            message: response.statusText || `Request failed with HTTP status ${response.status}`,
            timestamp: new Date().toISOString(),
          };
        }

        // Notify user-facing notification hooks
        this.notifyErrorHooks(errorDetail, response.status);

        throw new ApiClientError(
          errorDetail.code,
          errorDetail.message,
          response.status,
          errorDetail.details,
          errorDetail.timestamp
        );
      }

      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error;
      }

      const networkError: ApiErrorDetail = {
        code: 'NETWORK_ERROR',
        message: error instanceof Error ? error.message : 'Network request failed or server is unreachable',
        details: { endpoint, originalError: String(error) },
        timestamp: new Date().toISOString(),
      };

      this.notifyErrorHooks(networkError, 0);

      throw new ApiClientError(
        networkError.code,
        networkError.message,
        0,
        networkError.details,
        networkError.timestamp
      );
    }
  }

  /**
   * Validate a scenario configuration without creating a simulation instance.
   * Endpoint: POST /api/v1/configs/validate
   */
  public async validateConfig(config: ScenarioConfig): Promise<ValidationResult> {
    return this.request<ValidationResult>('/configs/validate', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  /**
   * Create and initialize a new simulation instance from a scenario configuration.
   * Endpoint: POST /api/v1/simulations
   */
  public async createSimulation(config: ScenarioConfig): Promise<CreateSimulationResponse> {
    return this.request<CreateSimulationResponse>('/simulations', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  /**
   * Send a lifecycle control action (start, pause, resume, stop) to an active simulation.
   * Endpoint: POST /api/v1/simulations/{simulationId}/control
   */
  public async sendControlAction(
    simulationId: string,
    action: ControlAction
  ): Promise<ControlActionResponse> {
    return this.request<ControlActionResponse>(`/simulations/${encodeURIComponent(simulationId)}/control`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  }

  /**
   * Fetch current status and progress of a simulation.
   * Endpoint: GET /api/v1/simulations/{simulationId}
   */
  public async getSimulationStatus(simulationId: string): Promise<SimulationStatusResponse> {
    return this.request<SimulationStatusResponse>(`/simulations/${encodeURIComponent(simulationId)}`, {
      method: 'GET',
    });
  }

  /**
   * Retrieve final aggregated performance metrics for a completed simulation.
   * Endpoint: GET /api/v1/simulations/{simulationId}/metrics
   */
  public async getFinalMetrics(simulationId: string): Promise<FinalMetricsResponse> {
    return this.request<FinalMetricsResponse>(`/simulations/${encodeURIComponent(simulationId)}/metrics`, {
      method: 'GET',
    });
  }

  /**
   * Check backend health and version status.
   * Endpoint: GET /api/v1/health
   */
  public async healthCheck(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>('/health', {
      method: 'GET',
    });
  }
}

// Singleton default instance export
export const apiClient = new ApiClient();

// Standalone function exports for flexible consumption
export const validateConfig = (config: ScenarioConfig): Promise<ValidationResult> =>
  apiClient.validateConfig(config);

export const createSimulation = (config: ScenarioConfig): Promise<CreateSimulationResponse> =>
  apiClient.createSimulation(config);

export const sendControlAction = (
  simulationId: string,
  action: ControlAction
): Promise<ControlActionResponse> => apiClient.sendControlAction(simulationId, action);

export const getSimulationStatus = (simulationId: string): Promise<SimulationStatusResponse> =>
  apiClient.getSimulationStatus(simulationId);

export const getFinalMetrics = (simulationId: string): Promise<FinalMetricsResponse> =>
  apiClient.getFinalMetrics(simulationId);

export const healthCheck = (): Promise<HealthCheckResponse> => apiClient.healthCheck();

export const registerErrorHook = (hook: ErrorNotificationHook): (() => void) =>
  apiClient.registerErrorHook(hook);

export const removeErrorHook = (hook: ErrorNotificationHook): void => apiClient.removeErrorHook(hook);
