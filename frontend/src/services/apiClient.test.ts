/**
 * Unit Tests for ApiClient Service (ISSUE-041)
 */

import { ApiClient, ApiClientError } from './apiClient';
import { ScenarioConfig, ApiErrorDetail } from '../types/api';

describe('ApiClient Service', () => {
  let client: ApiClient;
  let originalFetch: typeof global.fetch;

  const mockSignalConfig: ScenarioConfig = {
    geometry: {
      intersectionType: 'fixed_time_signal',
    },
    simulation: {
      duration: 300,
    },
  };

  beforeEach(() => {
    client = new ApiClient('http://localhost:8000/api/v1');
    originalFetch = global.fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks?.();
  });

  test('configures base URL correctly', () => {
    expect(client.getBaseUrl()).toBe('http://localhost:8000/api/v1');
    client.setBaseUrl('http://localhost:8000/api/v1/');
    expect(client.getBaseUrl()).toBe('http://localhost:8000/api/v1');
  });

  test('validateConfig posts configuration to /configs/validate and returns result', async () => {
    const mockResponse = {
      valid: true,
      resolvedConfig: mockSignalConfig,
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    } as Response);

    const result = await client.validateConfig(mockSignalConfig);

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/configs/validate',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(mockSignalConfig),
      })
    );
    expect(result.valid).toBe(true);
    expect(result.resolvedConfig).toEqual(mockSignalConfig);
  });

  test('createSimulation posts configuration to /simulations and returns simulation ID', async () => {
    const mockResponse = {
      simulationId: 'sim_123456',
      status: 'initializing',
      createdAt: '2026-07-30T12:00:00Z',
      config: mockSignalConfig,
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockResponse,
    } as Response);

    const result = await client.createSimulation(mockSignalConfig);

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/simulations',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(mockSignalConfig),
      })
    );
    expect(result.simulationId).toBe('sim_123456');
    expect(result.status).toBe('initializing');
  });

  test('sendControlAction posts action to /simulations/{id}/control', async () => {
    const mockResponse = {
      simulationId: 'sim_123456',
      previousStatus: 'initializing',
      currentStatus: 'running',
      timestamp: '2026-07-30T12:00:01Z',
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    } as Response);

    const result = await client.sendControlAction('sim_123456', 'start');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/simulations/sim_123456/control',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ action: 'start' }),
      })
    );
    expect(result.currentStatus).toBe('running');
  });

  test('getFinalMetrics fetches report from /simulations/{id}/metrics', async () => {
    const mockResponse = {
      simulationId: 'sim_123456',
      controllerType: 'fixed_time_signal',
      status: 'completed',
      metrics: {
        average_wait_time: { value: 15.2, unit: 'seconds' },
        throughput: { value: 210, unit: 'vehicles' },
      },
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    } as Response);

    const result = await client.getFinalMetrics('sim_123456');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/simulations/sim_123456/metrics',
      expect.objectContaining({
        method: 'GET',
      })
    );
    expect(result.metrics.average_wait_time.value).toBe(15.2);
  });

  test('handles HTTP request failures and triggers error notification hooks', async () => {
    const mockErrorPayload = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid duration value',
        details: { path: 'simulation.duration' },
        timestamp: '2026-07-30T12:00:00Z',
      },
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => mockErrorPayload,
    } as Response);

    const errorHook = jest.fn();
    client.registerErrorHook(errorHook);

    await expect(client.validateConfig(mockSignalConfig)).rejects.toThrow(ApiClientError);

    expect(errorHook).toHaveBeenCalledWith(
      expect.objectContaining({
        code: 'VALIDATION_ERROR',
        message: 'Invalid duration value',
      }),
      400
    );
  });

  test('handles network exceptions and triggers NETWORK_ERROR notification hook', async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    let capturedError: ApiErrorDetail | undefined;
    client.registerErrorHook((error) => {
      capturedError = error;
    });

    await expect(client.healthCheck()).rejects.toThrow(ApiClientError);

    expect(capturedError).toBeDefined();
    expect(capturedError?.code).toBe('NETWORK_ERROR');
    expect(capturedError?.message).toBe('Failed to fetch');
  });
});
