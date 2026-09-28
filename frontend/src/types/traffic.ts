export interface TrafficInputData {
  distance_a_cm: number;
  speed_a_kmh: number;
  vehicle_count_a: number;
  distance_b_cm: number;
  speed_b_kmh: number;
  vehicle_count_b: number;
  source?: string;
  prev_distance_a_cm?: number | null;
  prev_distance_b_cm?: number | null;
}

export interface EngineeredFeatures {
  distance_a_cm: number;
  distance_b_cm: number;
  speed_a_kmh: number;
  speed_b_kmh: number;
  speed_a_cms: number;
  speed_b_cms: number;
  vehicle_count_a: number;
  vehicle_count_b: number;
  total_vehicles: number;
  traffic_density: "LOW" | "MEDIUM" | "HIGH";
  ttc_a_seconds: number | null;
  ttc_b_seconds: number | null;
  ttc_a_display: string;
  ttc_b_display: string;
  stopping_dist_a_cm?: number;
  stopping_dist_b_cm?: number;
  simultaneous_vehicle_presence: boolean;
  simultaneous_approach: boolean;
  relative_urgency: "SIDE_A_URGENT" | "SIDE_B_URGENT" | "EQUAL_URGENT" | "NEITHER";
  relative_arrival_time_diff_sec: number | null;
  distance_change_a_cm: number | null;
  distance_change_b_cm: number | null;
  conflict_potential: "NONE" | "LOW" | "MODERATE" | "CRITICAL";
}

export interface AIPredictionResult {
  predicted_risk: "SAFE" | "CAUTION" | "HIGH_RISK" | "COLLISION_RISK";
  confidence_score: number | null;
  class_probabilities: Record<string, number>;
  model_name: string;
  model_version: string;
  feature_contributions?: Record<string, number>;
}

export interface SafetyAssessmentResult {
  final_safety_risk: "SAFE" | "CAUTION" | "HIGH_RISK" | "COLLISION_RISK";
  override_applied: boolean;
  override_reason: string | null;
  warning_level: string;
  warning_message: string;
}

export interface TrafficRecommendationResult {
  side_a_action: "PROCEED" | "PROCEED WITH CAUTION" | "WAIT";
  side_b_action: "PROCEED" | "PROCEED WITH CAUTION" | "WAIT";
  recommendation_summary: string;
  primary_reason: string;
  contributing_factors: string[];
}

export interface TrafficAnalysisResponse {
  id?: number;
  timestamp: string;
  source: string;
  input: TrafficInputData;
  features: EngineeredFeatures;
  ai_prediction: AIPredictionResult;
  safety_assessment: SafetyAssessmentResult;
  traffic_recommendation: TrafficRecommendationResult;
}

export interface HistoryEventItem {
  id: number;
  timestamp: string;
  source: string;
  distance_a: number;
  distance_b: number;
  speed_a: number;
  speed_b: number;
  vehicle_count_a: number;
  vehicle_count_b: number;
  ttc_a: number | null;
  ttc_b: number | null;
  traffic_density: string;
  ai_risk: string;
  final_risk: string;
  warning: string;
  side_a_action: string;
  side_b_action: string;
  recommendation: string;
  explanation: string;
  raw_features?: any;
}

export interface AnalyticsSummary {
  total_events: number;
  has_data: boolean;
  risk_distribution: Record<string, number>;
  density_distribution: Record<string, number>;
  average_speed_a: number;
  average_speed_b: number;
  average_distance_a: number;
  average_distance_b: number;
  safe_count: number;
  caution_count: number;
  high_risk_count: number;
  collision_risk_count: number;
}

export interface ModelInfo {
  model_name: string;
  model_version: string;
  algorithm: string;
  parameters: Record<string, any>;
  training_date: string;
  dataset_name: string;
  dataset_type: string;
  academic_disclaimer: string;
  sample_counts: {
    total_samples: number;
    train_samples: number;
    test_samples: number;
  };
  metrics: {
    accuracy: number;
    precision_macro: number;
    recall_macro: number;
    f1_macro: number;
    precision_weighted: number;
    recall_weighted: number;
    f1_weighted: number;
  };
  confusion_matrix: {
    labels: string[];
    matrix: number[][];
  };
  per_class_metrics: Record<string, {
    precision: number;
    recall: number;
    f1_score: number;
    support: number;
  }>;
  feature_importances: Record<string, number>;
}
