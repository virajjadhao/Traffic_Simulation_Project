/**
 * Canonical API Types for Traffic Intersection Simulation Dashboard
 * Aligned with Shared Contracts:
 * - 05-snapshot-contract.md
 * - 06-scenario-configuration-contract.md
 * - 07-metric-contract.md
 * - 08-communication-contract.md
 */

export type ControllerType = 'fixed_time_signal' | 'roundabout';

export type SimulationStatus =
  | 'initializing'
  | 'running'
  | 'paused'
  | 'stopped'
  | 'completed'
  | 'error';

export type ControlAction = 'start' | 'pause' | 'resume' | 'stop';

export type Direction = 'north' | 'south' | 'east' | 'west';

export interface DirectionalSplit {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface TurnProbabilities {
  left: number;
  straight: number;
  right: number;
}

export interface RangeValue {
  min: number;
  max: number;
}

export interface ApproachConfig {
  direction: Direction;
  lanes?: number;
  speedLimit?: number;
}

export interface FixedTimeControllerConfig {
  greenTime?: number;
  yellowTime?: number;
  allRedTime?: number;
  phaseSequence?: string[];
  offset?: number;
}

export interface RoundaboutControllerConfig {
  innerRadius?: number;
  outerRadius?: number;
  circulatingLanes?: number;
  criticalGap?: number;
  followUpTime?: number;
  entrySpeed?: number;
  circulatingSpeed?: number;
}

export type ControllerConfig = FixedTimeControllerConfig | RoundaboutControllerConfig;

export interface SimulationParameters {
  duration?: number;
  timeStep?: number;
  warmupTime?: number;
  randomSeed?: number;
  snapshotFrequency?: number;
}

export interface TrafficParameters {
  totalVehicles?: number;
  arrivalRate?: number;
  arrivalDistribution?: 'poisson' | 'uniform' | 'burst';
  directionalSplit?: DirectionalSplit;
  turnProbabilities?: TurnProbabilities;
}

export interface GeometryParameters {
  intersectionType: ControllerType;
  intersectionCenter?: { x: number; y: number };
}

export interface RoadParameters {
  approachLength?: number;
  laneWidth?: number;
  lanesPerApproach?: number;
  speedLimit?: number;
  approaches?: ApproachConfig[];
}

export interface VehicleGenerationParameters {
  vehicleLength?: RangeValue;
  vehicleWidth?: RangeValue;
  desiredSpeed?: RangeValue;
  maxAcceleration?: number;
  comfortDeceleration?: number;
  minimumGap?: number;
  desiredTimeHeadway?: number;
  idmDelta?: number;
}

export interface MetricParameters {
  enabled?: string[];
  updateFrequency?: number;
  rollingWindowSize?: number;
  waitSpeedThreshold?: number;
  stopSpeedThreshold?: number;
}

export interface VisualizationParameters {
  canvasWidth?: number;
  canvasHeight?: number;
  pixelsPerMeter?: number;
  showVehicleIds?: boolean;
  showQueueLengths?: boolean;
  colorScheme?: 'default' | 'colorblind';
  trailLength?: number;
}

export interface ScenarioConfig {
  simulation?: SimulationParameters;
  traffic?: TrafficParameters;
  geometry: GeometryParameters;
  roads?: RoadParameters;
  vehicleGeneration?: VehicleGenerationParameters;
  controller?: ControllerConfig;
  metrics?: MetricParameters;
  visualization?: VisualizationParameters;
}

// --- API Request & Response Payload Interfaces ---

export interface ValidationErrorDetail {
  path: string;
  message: string;
  value?: unknown;
  constraint?: unknown;
}

export interface ValidationResult {
  valid: boolean;
  errors?: ValidationErrorDetail[];
  resolvedConfig?: ScenarioConfig;
}

export interface CreateSimulationResponse {
  simulationId: string;
  configId?: string;
  status: SimulationStatus;
  createdAt: string;
  config: ScenarioConfig;
}

export interface SimulationStatusResponse {
  simulationId: string;
  status: SimulationStatus;
  progress: number;
  currentTick: number;
  totalTicks: number;
  elapsedTime: number;
  totalTime: number;
}

export interface ControlActionRequest {
  action: ControlAction;
}

export interface ControlActionResponse {
  simulationId: string;
  previousStatus: SimulationStatus;
  currentStatus: SimulationStatus;
  timestamp: string;
}

export interface MetricDetail {
  value: number;
  unit: string;
  description?: string;
  sampleSize?: number;
  confidence?: 'low' | 'medium' | 'high';
  rate?: number;
  rateUnit?: string;
  average?: number;
  maximum?: number;
  percentile95?: number;
  perDirection?: Record<string, unknown>;
  median_travel_time?: number;
  p95_travel_time?: number;
  [key: string]: unknown;
}

export interface FinalMetricsResponse {
  simulationId: string;
  configId?: string;
  controllerType: ControllerType;
  status: SimulationStatus;
  simulationDuration?: number;
  effectiveDuration?: number;
  totalVehiclesProcessed?: number;
  computedAt?: string;
  metrics: Record<string, MetricDetail>;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  uptime: number;
  timestamp: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: unknown;
  timestamp?: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export type ErrorNotificationHook = (error: ApiErrorDetail, httpStatus?: number) => void;
