import axios, { AxiosInstance, AxiosError } from 'axios';

// API Base URLs - pointing to Python microservices
const API_URLS = {
  auth: process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:8000',
  user: process.env.NEXT_PUBLIC_USER_API_URL || 'http://localhost:8001',
  wallet: process.env.NEXT_PUBLIC_WALLET_API_URL || 'http://localhost:8002',
  funding: process.env.NEXT_PUBLIC_FUNDING_API_URL || 'http://localhost:8003',
};

// Create axios instances for each service
const createApiClient = (baseURL: string): AxiosInstance => {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - add JWT token
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - handle errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        // Unauthorized - clear token
        // Note: Don't redirect here, let the layout handle it
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
      return Promise.reject(error);
    }
  );

  return client;
};

export const authApi = createApiClient(API_URLS.auth);
export const userApi = createApiClient(API_URLS.user);
export const walletApi = createApiClient(API_URLS.wallet);
export const fundingApi = createApiClient(API_URLS.funding);

// Types
export interface User {
  id: string;
  email: string;
  username: string;
  phone: string;
  is_admin: boolean;
  created_at: string;
}

export interface Wallet {
  id: string;
  user_id: string;
  currency: 'NAIRA' | 'USDT';
  balance: string;
  balance_formatted?: string;
  total_deposited: string;
  total_won: string;
  total_withdrawn: string;
  is_blocked: boolean;
  block_reason?: string | null;
  referral_code: string;
  has_won_before: boolean;
  consecutive_cancellations?: number;
  consecutive_misses?: number;
  wallet_address?: string | null;  // For USDT wallet
  bank_details_id?: string | null;  // For NAIRA wallet
  created_at: string;
}

export interface Game {
  id: string;
  title: string;
  home_team: string;
  away_team: string;
  scheduled_time: string;
  betting_closes_at: string;
  status: string;
  winner: string | null;
  home_total_naira: number;
  away_total_naira: number;
  home_total_usdt: number;
  away_total_usdt: number;
}

export interface MatchedUser {
  username: string;
  phone: string;
  amount: string;
  proof_uploaded: boolean;
  proof_confirmed: boolean;
  pair_id: string;
}

export interface FundingRequest {
  id: string;
  amount: string;
  amount_remaining: string;
  currency: string;
  is_fully_matched: boolean;
  is_completed: boolean;
  matched_users: MatchedUser[];
  requested_at: string;
  matched_at: string | null;
}

export interface WithdrawalRequest {
  id: string;
  amount: string;
  amount_remaining: string;
  currency: string;
  is_fully_matched: boolean;
  is_completed: boolean;
  matched_users: MatchedUser[];
  requested_at: string;
  matched_at: string | null;
}

export interface MergeCycleInfo {
  has_cycle: boolean;
  merge_time?: string;
  cutoff_time?: string;
  can_create_request?: boolean;
  time_until_merge_seconds?: number;
  status?: string;
}

export interface AdminWallet {
  id: string;
  wallet_type: 'funding_pool' | 'platform_fees';
  currency: 'NAIRA' | 'USDT';
  balance: string;
  total_funded?: string;
  total_received?: string;
  total_fees_collected?: string;
  created_at: string;
}

export interface MergeCycleStats {
  id: string;
  scheduled_time: string;
  cutoff_time: string;
  status: string;
  total_funding_requests: number;
  total_withdrawal_requests: number;
  matched_pairs: number;
  unmatched_funding: number;
  unmatched_withdrawal: number;
  admin_funded: number;
  admin_withdrew: number;
  created_at: string;
  executed_at?: string;
}

export interface AdminDashboard {
  next_merge_cycle: MergeCycleStats | null;
  admin_wallets: AdminWallet[];
  unmatched_counts: {
    funding_naira: number;
    funding_usdt: number;
    withdrawal_naira: number;
    withdrawal_usdt: number;
  };
  recent_cycles: MergeCycleStats[];
}

export interface UnmatchedRequest {
  id: string;
  user_id: string;
  username: string;
  phone: string;
  amount: string;
  amount_remaining: string;
  requested_at: string;
}

// Auth API
export const authService = {
  register: (data: {
    email: string;
    username: string;
    first_name: string;
    last_name: string;
    phone: string;
    password: string;
    referral_code?: string;
  }) => authApi.post('/register', data),

  login: (email: string, password: string) =>
    authApi.post<{ access_token: string; user: User }>('/login', { email, password }),

  refreshToken: (refresh_token: string) =>
    authApi.post('/refresh', { refresh_token }),
};

// User API
export const userService = {
  getProfile: () => userApi.get<User>('/me'),

  updateProfile: (data: { username?: string; phone?: string }) =>
    userApi.put('/me', data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    userApi.put('/password', data),
};

// Wallet API
export const walletService = {
  getWallets: () => walletApi.get<Wallet[]>('/wallets'),

  getWallet: (currency: 'NAIRA' | 'USDT') =>
    walletApi.get<Wallet>(`/wallets/${currency}`),

  getBalance: (currency: 'NAIRA' | 'USDT') =>
    walletApi.get<{ balance: number }>(`/balance/${currency}`),

  getTransactions: (currency: 'NAIRA' | 'USDT', limit?: number) =>
    walletApi.get(`/transactions/${currency}`, { params: { limit } }),

  // Bank account for NAIRA
  getNairaBankAccount: () =>
    walletApi.get('/wallet/naira/bank-account'),

  setNairaBankAccount: (data: {
    account_number: string
    account_name: string
    bank_name: string
  }) => walletApi.post('/wallet/naira/bank-account', data),

  // USDT wallet address
  getUsdtWalletAddress: () =>
    walletApi.get('/wallet/usdt/address'),

  setUsdtWalletAddress: (wallet_address: string) =>
    walletApi.post('/wallet/usdt/address', { wallet_address }),
};

// Funding API
export const fundingService = {
  createFundingRequest: (amount: number, currency: 'NAIRA' | 'USDT') =>
    fundingApi.post('/funding/request', null, { params: { amount, currency } }),

  createWithdrawalRequest: (amount: number, currency: 'NAIRA' | 'USDT') =>
    fundingApi.post('/withdrawal/request', null, { params: { amount, currency } }),

  getMyFundingRequests: () =>
    fundingApi.get<{ data: FundingRequest[] }>('/funding/my-requests'),

  getMyWithdrawalRequests: () =>
    fundingApi.get<{ data: WithdrawalRequest[] }>('/withdrawal/my-requests'),

  getNextMergeCycle: () =>
    fundingApi.get<{ data: MergeCycleInfo }>('/merge-cycle/next'),

  // Join merge cycle
  joinMergeCycle: () =>
    fundingApi.post('/merge-cycle/join'),

  getMergeCycleStatus: () =>
    fundingApi.get('/merge-cycle/my-status'),

  getMyActiveMatches: () =>
    fundingApi.get('/my-active-matches'),

  uploadProof: (pairId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return fundingApi.post(`/match-pair/${pairId}/upload-proof`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  confirmProof: (pairId: string) =>
    fundingApi.post(`/match-pair/${pairId}/confirm-proof`),

  requestExtension: (pairId: string) =>
    fundingApi.post(`/match-pair/${pairId}/request-extension`),

  cancelFundingRequest: (requestId: string) =>
    fundingApi.delete(`/funding/request/${requestId}/cancel`),

  cancelWithdrawalRequest: (requestId: string) =>
    fundingApi.delete(`/withdrawal/request/${requestId}/cancel`),
};

// Admin API
export const adminService = {
  getDashboard: () =>
    fundingApi.get<{ data: AdminDashboard }>('/admin/dashboard'),

  getUnmatchedRequests: (currency: 'NAIRA' | 'USDT') =>
    fundingApi.get<{ data: { funding_requests: UnmatchedRequest[]; withdrawal_requests: UnmatchedRequest[] } }>(
      '/admin/unmatched-requests',
      { params: { currency } }
    ),

  manualMatch: (fundingRequestId: string, withdrawalRequestId: string, amount: number) =>
    fundingApi.post('/admin/manual-match', null, {
      params: { funding_request_id: fundingRequestId, withdrawal_request_id: withdrawalRequestId, amount }
    }),

  matchWithAdminWallet: (requestId: string, requestType: 'funding' | 'withdrawal') =>
    fundingApi.post('/admin/match-with-admin-wallet', null, {
      params: { request_id: requestId, request_type: requestType }
    }),

  triggerMergeCycle: () =>
    fundingApi.post('/admin/trigger-merge-cycle'),
};

// Error handler
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;

    // Handle Pydantic validation errors (array of error objects)
    if (Array.isArray(data?.detail)) {
      const errors = data.detail.map((err: any) => {
        const field = err.loc?.[1] || err.loc?.[0] || 'field';
        const msg = err.msg || 'validation error';
        // Capitalize field name for better display
        const fieldName = field.charAt(0).toUpperCase() + field.slice(1);
        return `${fieldName}: ${msg}`;
      });
      return errors.join('\n');
    }

    // Handle custom error format with nested error object
    if (data?.detail && typeof data.detail === 'object') {
      if (data.detail.error) {
        return data.detail.error;
      }
      if (data.detail.message) {
        return data.detail.message;
      }
    }

    // Handle string error messages
    if (typeof data?.detail === 'string') {
      return data.detail;
    }

    if (typeof data?.error === 'string') {
      return data.error;
    }

    if (typeof data?.message === 'string') {
      return data.message;
    }

    // Fallback to error message with status code
    const statusText = error.response?.statusText || 'Error';
    const status = error.response?.status || '';
    return `${statusText}${status ? ` (${status})` : ''}: ${error.message || 'An unexpected error occurred'}`;
  }
  return 'An unexpected error occurred';
};
