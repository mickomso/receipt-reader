// API client for the Receipt Reader backend

import type { Receipt, ReceiptDetail, ReceiptListResponse } from './types';

const BASE = '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail ?? JSON.stringify(err);
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function uploadReceipt(file: File): Promise<Receipt> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/receipts`, { method: 'POST', body: form });
  return handleResponse<Receipt>(res);
}

export async function processReceipt(id: string): Promise<ReceiptDetail> {
  const res = await fetch(`${BASE}/receipts/${id}/process`, { method: 'POST' });
  return handleResponse<ReceiptDetail>(res);
}

export async function listReceipts(skip = 0, limit = 20): Promise<ReceiptListResponse> {
  const res = await fetch(`${BASE}/receipts?skip=${skip}&limit=${limit}`);
  return handleResponse<ReceiptListResponse>(res);
}

export async function getReceipt(id: string): Promise<ReceiptDetail> {
  const res = await fetch(`${BASE}/receipts/${id}`);
  return handleResponse<ReceiptDetail>(res);
}

export async function patchReceipt(id: string, patch: Record<string, unknown>): Promise<ReceiptDetail> {
  const res = await fetch(`${BASE}/receipts/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch)
  });
  return handleResponse<ReceiptDetail>(res);
}

export async function confirmReceipt(
  id: string,
  corrections: Record<string, unknown> | null = null
): Promise<ReceiptDetail> {
  const res = await fetch(`${BASE}/receipts/${id}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ corrections })
  });
  return handleResponse<ReceiptDetail>(res);
}
