import { apiClient } from './client';
import { Port } from './ports';

export interface FreightRoute {
  id: string;
  route_code: string;
  origin_port_id: string;
  destination_port_id: string;
  default_vessel_class: string;
  distance_nm: number;
  typical_duration_days: number;
  origin_port?: Port;
  destination_port?: Port;
}

export interface FreightObservation {
  id: string;
  route_id: string;
  observation_date: string;
  freight_rate_usd_pmt: number;
  bunker_vlsfo_usd?: number;
  bunker_mgo_usd?: number;
  baltic_index_value?: number;
  congestion_origin_days?: number;
  congestion_dest_days?: number;
  is_interpolated: boolean;
  source_type: string;
}

export interface FreightForecast {
  id: string;
  route_id: string;
  vessel_class: string;
  model_type: string;
  horizon_days: number;
  target_date: string;
  predicted_p10: number;
  predicted_p50: number;
  predicted_p90: number;
  confidence_pct: number;
  volatility_index?: number;
  feature_attributions?: string;
  generated_at: string;
}

export interface BacktestResult {
  id: string;
  route_id: string;
  model_type: string;
  horizon_days: number;
  test_start_date: string;
  test_end_date: string;
  sample_count: number;
  mae: number;
  rmse: number;
  mape: number;
  directional_accuracy_pct: number;
  pinball_loss_p10: number;
  pinball_loss_p50: number;
  pinball_loss_p90: number;
  evaluated_at: string;
}

export interface GenerateForecastsInput {
  route_id: string;
  vessel_class?: string;
  model_type?: string;
  horizons?: number[];
}

export const freightApi = {
  getRoutes: () => apiClient<FreightRoute[]>('/freight/routes'),
  getObservations: (routeId: string, days?: number) =>
    apiClient<FreightObservation[]>(`/freight/routes/${routeId}/observations${days ? `?days=${days}` : ''}`),
  getForecasts: (routeId: string, modelType?: string) =>
    apiClient<FreightForecast[]>(`/freight/routes/${routeId}/forecasts${modelType ? `?model_type=${modelType}` : ''}`),
  getBacktestResults: (routeId: string) =>
    apiClient<BacktestResult[]>(`/freight/routes/${routeId}/backtest`),
  generateForecasts: (input: GenerateForecastsInput) =>
    apiClient<FreightForecast[]>('/freight/forecasts/generate', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
};
