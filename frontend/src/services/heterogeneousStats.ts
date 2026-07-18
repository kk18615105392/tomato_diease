import axios from "axios";

export type Exp1Row = {
  group: string;
  mix_ratio: string;
  uncertainty: boolean;
  tomato_acc: number;
  tomato_f1: number;
  fruit_acc: number | null;
  fruit_f1: number | null;
  note: string;
  best?: boolean;
};

export type Exp2Row = {
  group: string;
  method: string;
  tomato_acc: number;
  fruit_acc: number;
  cross_acc: number;
  mmd: number;
  note: string;
  best?: boolean;
};

export type Exp3Row = {
  group: string;
  method: string;
  source_acc: number;
  domain_disc_acc: number;
  cross_acc: number;
  note: string;
  best?: boolean;
};

export type Exp4Row = {
  group: string;
  method: string;
  tomato_test: number;
  fruit_test: number;
  cross_test: number;
  note: string;
  best?: boolean;
};

export type HeterogeneousStats = {
  chapter?: string;
  meta?: {
    title: string;
    hypothesis: string;
    pipeline: string[];
    best_cross_acc: number;
    best_method: string;
  };
  dataset: {
    tomato_base: number;
    tropical_fruit: number;
    mixed_total: number;
    tomato_label: string;
    tropical_label: string;
    mixed_label: string;
    description: string;
    source_domain?: string;
    target_domain?: string;
    shared_encoder?: string;
  };
  epoch_comparison: {
    x_label: string;
    y_label: string;
    baseline: {
      name: string;
      color: string;
      final_accuracy: number;
      data: { epoch: number; accuracy: number }[];
    };
    enhanced: {
      name: string;
      color: string;
      final_accuracy: number;
      data: { epoch: number; accuracy: number }[];
    };
    improvement_abs: number;
    improvement_rel: number;
  };
  robustness_radar: {
    indicators: { name: string; max: number }[];
    baseline: { name: string; values: number[] };
    enhanced: { name: string; values: number[] };
  };
  exp1_mix_ratio?: Exp1Row[];
  exp2_mmd?: Exp2Row[];
  exp3_adversarial?: Exp3Row[];
  exp4_ablation?: Exp4Row[];
  summary: string;
  note?: string;
};

export async function fetchHeterogeneousStats(): Promise<HeterogeneousStats> {
  const { data } = await axios.get<HeterogeneousStats>("/api/stats/heterogeneous");
  return data;
}
