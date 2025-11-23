import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Wallet, walletService } from './api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

interface WalletState {
  selectedCurrency: 'NAIRA' | 'USDT';
  nairaWallet: Wallet | null;
  usdtWallet: Wallet | null;
  setSelectedCurrency: (currency: 'NAIRA' | 'USDT') => void;
  setNairaWallet: (wallet: Wallet) => void;
  setUsdtWallet: (wallet: Wallet) => void;
  getCurrentWallet: () => Wallet | null;
  fetchWallets: () => Promise<void>;
}

// Auth Store
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (token, user) => {
        localStorage.setItem('token', token);
        set({ token, user, isAuthenticated: true });
      },

      logout: () => {
        localStorage.removeItem('token');
        set({ token: null, user: null, isAuthenticated: false });
      },

      updateUser: (userData) => {
        const currentUser = get().user;
        if (currentUser) {
          set({ user: { ...currentUser, ...userData } });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Wallet Store
export const useWalletStore = create<WalletState>()(
  persist(
    (set, get) => ({
      selectedCurrency: 'NAIRA',
      nairaWallet: null,
      usdtWallet: null,

      setSelectedCurrency: (currency) => set({ selectedCurrency: currency }),

      setNairaWallet: (wallet) => set({ nairaWallet: wallet }),

      setUsdtWallet: (wallet) => set({ usdtWallet: wallet }),

      getCurrentWallet: () => {
        const state = get();
        return state.selectedCurrency === 'NAIRA' ? state.nairaWallet : state.usdtWallet;
      },

      fetchWallets: async () => {
        try {
          // Fetch from user service to get blocking info
          const userResponse = await fetch('http://localhost:8001/me', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          });
          const userData = await userResponse.json();

          if (userData.data?.wallets) {
            const nairaData = userData.data.wallets.naira;
            const usdtData = userData.data.wallets.usdt;

            set({
              nairaWallet: nairaData.id ? {
                id: nairaData.id,
                user_id: userData.data.user.id,
                currency: 'NAIRA',
                balance: nairaData.balance,
                total_deposited: '0',
                total_won: '0',
                total_withdrawn: '0',
                is_blocked: nairaData.is_blocked,
                block_reason: nairaData.block_reason,
                referral_code: userData.data.user.referral_code,
                has_won_before: false,
                created_at: new Date().toISOString(),
              } as Wallet : null,
              usdtWallet: usdtData.id ? {
                id: usdtData.id,
                user_id: userData.data.user.id,
                currency: 'USDT',
                balance: usdtData.balance,
                total_deposited: '0',
                total_won: '0',
                total_withdrawn: '0',
                is_blocked: usdtData.is_blocked,
                block_reason: usdtData.block_reason,
                referral_code: userData.data.user.referral_code,
                has_won_before: false,
                created_at: new Date().toISOString(),
              } as Wallet : null,
            });
          }
        } catch (error) {
          console.error('Failed to fetch wallets:', error);
        }
      },
    }),
    {
      name: 'wallet-storage',
    }
  )
);
