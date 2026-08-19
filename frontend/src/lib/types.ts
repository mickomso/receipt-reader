// TypeScript types mirroring the backend API contract

export type ReceiptStatus =
  | 'uploaded'
  | 'processing'
  | 'extracted'
  | 'needs_review'
  | 'confirmed'
  | 'failed';

export interface TaxDetail {
  name: string | null;
  rate: string | null;
  base: string | null;
  amount: string | null;
}

export interface ReceiptItem {
  id: string;
  position: number;
  raw_description: string;
  normalized_description: string | null;
  quantity: string | null;
  unit: string | null;
  unit_price: string | null;
  price_per_kg: string | null;
  discount: string | null;
  total_price: string | null;
  confidence: number | null;
  needs_review: boolean;
  line_valid: boolean | null;
  line_difference: string | null;
}

export interface ReceiptTotals {
  subtotal: string | null;
  taxes: TaxDetail[];
  total: string | null;
  calculated_total: string | null;
  difference: string | null;
  totals_valid: boolean | null;
}

export interface Receipt {
  id: string;
  filename: string;
  status: ReceiptStatus;
  commerce: string | null;
  date: string | null;
  time: string | null;
  currency: string;
  ticket_number: string | null;
  payment_method: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReceiptDetail extends Receipt {
  items: ReceiptItem[];
  totals: ReceiptTotals | null;
}

export interface ReceiptListResponse {
  items: Receipt[];
  total: number;
  skip: number;
  limit: number;
}

export interface ApiError {
  detail: string;
}
