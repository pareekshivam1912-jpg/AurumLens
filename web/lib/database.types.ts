export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.18"
  }
  public: {
    Tables: {
      audit_log: {
        Row: {
          action: string
          actor: string
          at: string
          detail: Json | null
          id: number
        }
        Insert: {
          action: string
          actor: string
          at?: string
          detail?: Json | null
          id?: never
        }
        Update: {
          action?: string
          actor?: string
          at?: string
          detail?: Json | null
          id?: never
        }
        Relationships: []
      }
      backtest_run: {
        Row: {
          config_version: string
          created_at: string
          dataset_version: string
          folds: Json
          is_holdout: boolean
          run_id: string
          summary: Json | null
        }
        Insert: {
          config_version: string
          created_at?: string
          dataset_version: string
          folds: Json
          is_holdout?: boolean
          run_id?: string
          summary?: Json | null
        }
        Update: {
          config_version?: string
          created_at?: string
          dataset_version?: string
          folds?: Json
          is_holdout?: boolean
          run_id?: string
          summary?: Json | null
        }
        Relationships: []
      }
      contract: {
        Row: {
          contract_id: string
          expiry_date: string
          first_seen: string | null
          last_seen: string | null
          symbol: string
        }
        Insert: {
          contract_id: string
          expiry_date: string
          first_seen?: string | null
          last_seen?: string | null
          symbol: string
        }
        Update: {
          contract_id?: string
          expiry_date?: string
          first_seen?: string | null
          last_seen?: string | null
          symbol?: string
        }
        Relationships: [
          {
            foreignKeyName: "contract_symbol_fkey"
            columns: ["symbol"]
            isOneToOne: false
            referencedRelation: "contract_spec"
            referencedColumns: ["symbol"]
          },
        ]
      }
      contract_spec: {
        Row: {
          expiry_rule: string | null
          field_status: Json
          purity: number | null
          quote_basis_g: number | null
          source_reference: string | null
          symbol: string
          tender_days: number | null
          tick_size: number | null
          trading_unit_g: number | null
          verified_at: string | null
        }
        Insert: {
          expiry_rule?: string | null
          field_status?: Json
          purity?: number | null
          quote_basis_g?: number | null
          source_reference?: string | null
          symbol: string
          tender_days?: number | null
          tick_size?: number | null
          trading_unit_g?: number | null
          verified_at?: string | null
        }
        Update: {
          expiry_rule?: string | null
          field_status?: Json
          purity?: number | null
          quote_basis_g?: number | null
          source_reference?: string | null
          symbol?: string
          tender_days?: number | null
          tick_size?: number | null
          trading_unit_g?: number | null
          verified_at?: string | null
        }
        Relationships: []
      }
      cost_line: {
        Row: {
          amount_inr: number
          component: string
          id: number
          leg: string | null
          side: string | null
          signal_id: string | null
          trade_id: string | null
        }
        Insert: {
          amount_inr: number
          component: string
          id?: never
          leg?: string | null
          side?: string | null
          signal_id?: string | null
          trade_id?: string | null
        }
        Update: {
          amount_inr?: number
          component?: string
          id?: never
          leg?: string | null
          side?: string | null
          signal_id?: string | null
          trade_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "cost_line_signal_id_fkey"
            columns: ["signal_id"]
            isOneToOne: false
            referencedRelation: "signal"
            referencedColumns: ["signal_id"]
          },
        ]
      }
      daily_price: {
        Row: {
          close: number | null
          contract_id: string
          dataset_version: string
          file_id: number
          high: number | null
          low: number | null
          normalized_price: number | null
          open: number | null
          open_interest: number | null
          price_quality: string
          price_source: string | null
          price_used: number | null
          quality_reason: string | null
          settlement: number | null
          trade_date: string
          volume: number | null
        }
        Insert: {
          close?: number | null
          contract_id: string
          dataset_version: string
          file_id: number
          high?: number | null
          low?: number | null
          normalized_price?: number | null
          open?: number | null
          open_interest?: number | null
          price_quality: string
          price_source?: string | null
          price_used?: number | null
          quality_reason?: string | null
          settlement?: number | null
          trade_date: string
          volume?: number | null
        }
        Update: {
          close?: number | null
          contract_id?: string
          dataset_version?: string
          file_id?: number
          high?: number | null
          low?: number | null
          normalized_price?: number | null
          open?: number | null
          open_interest?: number | null
          price_quality?: string
          price_source?: string | null
          price_used?: number | null
          quality_reason?: string | null
          settlement?: number | null
          trade_date?: string
          volume?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "daily_price_contract_id_fkey"
            columns: ["contract_id"]
            isOneToOne: false
            referencedRelation: "contract"
            referencedColumns: ["contract_id"]
          },
          {
            foreignKeyName: "daily_price_file_id_fkey"
            columns: ["file_id"]
            isOneToOne: false
            referencedRelation: "source_file"
            referencedColumns: ["file_id"]
          },
        ]
      }
      gate_result: {
        Row: {
          config_version: string
          gate: string
          gate_no: number
          margin: number | null
          pair_id: string
          passed: boolean
          reason_code: string | null
          threshold: number | null
          trade_date: string
          value: number | null
        }
        Insert: {
          config_version: string
          gate: string
          gate_no: number
          margin?: number | null
          pair_id: string
          passed: boolean
          reason_code?: string | null
          threshold?: number | null
          trade_date: string
          value?: number | null
        }
        Update: {
          config_version?: string
          gate?: string
          gate_no?: number
          margin?: number | null
          pair_id?: string
          passed?: boolean
          reason_code?: string | null
          threshold?: number | null
          trade_date?: string
          value?: number | null
        }
        Relationships: []
      }
      market_event: {
        Row: {
          category: string | null
          event_date: string
          id: number
          label: string
          source: string | null
          verified: boolean
        }
        Insert: {
          category?: string | null
          event_date: string
          id?: never
          label: string
          source?: string | null
          verified?: boolean
        }
        Update: {
          category?: string | null
          event_date?: string
          id?: never
          label?: string
          source?: string | null
          verified?: boolean
        }
        Relationships: []
      }
      pair_daily: {
        Row: {
          buffer_inr: number | null
          carry_adj: number | null
          carry_rate: number | null
          carry_source: string | null
          config_version: string
          cost_total_inr: number | null
          dataset_version: string
          expected_convergence_inr: number | null
          expiry_gap_days: number | null
          leg_a_contract_id: string
          leg_b_contract_id: string
          log_spread_adj: number | null
          log_spread_raw: number | null
          lots_a: number | null
          lots_b: number | null
          net_edge_inr: number | null
          norm_a: number | null
          norm_b: number | null
          pair_id: string
          residual_fine_g: number | null
          rich_leg: string | null
          roll_mean: number | null
          roll_std: number | null
          slippage_inr: number | null
          trade_date: string
          zscore: number | null
        }
        Insert: {
          buffer_inr?: number | null
          carry_adj?: number | null
          carry_rate?: number | null
          carry_source?: string | null
          config_version: string
          cost_total_inr?: number | null
          dataset_version: string
          expected_convergence_inr?: number | null
          expiry_gap_days?: number | null
          leg_a_contract_id: string
          leg_b_contract_id: string
          log_spread_adj?: number | null
          log_spread_raw?: number | null
          lots_a?: number | null
          lots_b?: number | null
          net_edge_inr?: number | null
          norm_a?: number | null
          norm_b?: number | null
          pair_id: string
          residual_fine_g?: number | null
          rich_leg?: string | null
          roll_mean?: number | null
          roll_std?: number | null
          slippage_inr?: number | null
          trade_date: string
          zscore?: number | null
        }
        Update: {
          buffer_inr?: number | null
          carry_adj?: number | null
          carry_rate?: number | null
          carry_source?: string | null
          config_version?: string
          cost_total_inr?: number | null
          dataset_version?: string
          expected_convergence_inr?: number | null
          expiry_gap_days?: number | null
          leg_a_contract_id?: string
          leg_b_contract_id?: string
          log_spread_adj?: number | null
          log_spread_raw?: number | null
          lots_a?: number | null
          lots_b?: number | null
          net_edge_inr?: number | null
          norm_a?: number | null
          norm_b?: number | null
          pair_id?: string
          residual_fine_g?: number | null
          rich_leg?: string | null
          roll_mean?: number | null
          roll_std?: number | null
          slippage_inr?: number | null
          trade_date?: string
          zscore?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "pair_daily_leg_a_contract_id_fkey"
            columns: ["leg_a_contract_id"]
            isOneToOne: false
            referencedRelation: "contract"
            referencedColumns: ["contract_id"]
          },
          {
            foreignKeyName: "pair_daily_leg_b_contract_id_fkey"
            columns: ["leg_b_contract_id"]
            isOneToOne: false
            referencedRelation: "contract"
            referencedColumns: ["contract_id"]
          },
        ]
      }
      paper_position: {
        Row: {
          closed_at: string | null
          legs: Json
          opened_at: string | null
          pnl: Json | null
          position_id: string
          signal_id: string
          state: string
        }
        Insert: {
          closed_at?: string | null
          legs: Json
          opened_at?: string | null
          pnl?: Json | null
          position_id?: string
          signal_id: string
          state: string
        }
        Update: {
          closed_at?: string | null
          legs?: Json
          opened_at?: string | null
          pnl?: Json | null
          position_id?: string
          signal_id?: string
          state?: string
        }
        Relationships: [
          {
            foreignKeyName: "paper_position_signal_id_fkey"
            columns: ["signal_id"]
            isOneToOne: true
            referencedRelation: "signal"
            referencedColumns: ["signal_id"]
          },
        ]
      }
      signal: {
        Row: {
          config_version: string
          created_at: string
          dataset_version: string
          direction: string | null
          evidence: Json
          near_miss_score: number | null
          pair_id: string
          reason_codes: string[]
          signal_id: string
          status: string
          trade_date: string
        }
        Insert: {
          config_version: string
          created_at?: string
          dataset_version: string
          direction?: string | null
          evidence: Json
          near_miss_score?: number | null
          pair_id: string
          reason_codes?: string[]
          signal_id?: string
          status: string
          trade_date: string
        }
        Update: {
          config_version?: string
          created_at?: string
          dataset_version?: string
          direction?: string | null
          evidence?: Json
          near_miss_score?: number | null
          pair_id?: string
          reason_codes?: string[]
          signal_id?: string
          status?: string
          trade_date?: string
        }
        Relationships: []
      }
      source_file: {
        Row: {
          adapter: string
          fetched_at: string
          file_id: number
          reject_reason: string | null
          requested_date: string
          returned_date: string | null
          sha256: string
          status: string
          storage_path: string
        }
        Insert: {
          adapter: string
          fetched_at?: string
          file_id?: never
          reject_reason?: string | null
          requested_date: string
          returned_date?: string | null
          sha256: string
          status: string
          storage_path: string
        }
        Update: {
          adapter?: string
          fetched_at?: string
          file_id?: never
          reject_reason?: string | null
          requested_date?: string
          returned_date?: string | null
          sha256?: string
          status?: string
          storage_path?: string
        }
        Relationships: []
      }
      trade: {
        Row: {
          costs: number | null
          entry_date: string
          exit_date: string | null
          exit_reason: string | null
          gross_pnl: number | null
          legs: Json
          net_pnl: number | null
          pair_id: string
          residual_gold_pnl: number | null
          run_id: string | null
          slippage: number | null
          strategy_pnl: number | null
          trade_id: string
        }
        Insert: {
          costs?: number | null
          entry_date: string
          exit_date?: string | null
          exit_reason?: string | null
          gross_pnl?: number | null
          legs: Json
          net_pnl?: number | null
          pair_id: string
          residual_gold_pnl?: number | null
          run_id?: string | null
          slippage?: number | null
          strategy_pnl?: number | null
          trade_id?: string
        }
        Update: {
          costs?: number | null
          entry_date?: string
          exit_date?: string | null
          exit_reason?: string | null
          gross_pnl?: number | null
          legs?: Json
          net_pnl?: number | null
          pair_id?: string
          residual_gold_pnl?: number | null
          run_id?: string | null
          slippage?: number | null
          strategy_pnl?: number | null
          trade_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "trade_run_id_fkey"
            columns: ["run_id"]
            isOneToOne: false
            referencedRelation: "backtest_run"
            referencedColumns: ["run_id"]
          },
        ]
      }
      trial: {
        Row: {
          params: Json
          run_id: string
          train_metric: number | null
          trial_id: string
        }
        Insert: {
          params: Json
          run_id: string
          train_metric?: number | null
          trial_id?: string
        }
        Update: {
          params?: Json
          run_id?: string
          train_metric?: number | null
          trial_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "trial_run_id_fkey"
            columns: ["run_id"]
            isOneToOne: false
            referencedRelation: "backtest_run"
            referencedColumns: ["run_id"]
          },
        ]
      }
    }
    Views: {
      v_latest_status: {
        Row: {
          config_version: string | null
          near_miss_score: number | null
          pair_id: string | null
          reason_codes: string[] | null
          status: string | null
          trade_date: string | null
        }
        Relationships: []
      }
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
