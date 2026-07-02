"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase/client";
import { signOut } from "@/services/auth/authService";
import {
  AppProfile,
  getCurrentAppProfile,
} from "@/services/profile/profileService";

type AuthContextType = {
  session: Session | null;
  profile: AppProfile | null;
  loading: boolean;
  refreshProfile: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
  session: null,
  profile: null,
  loading: true,
  refreshProfile: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<AppProfile | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshProfile() {
    const appProfile = await getCurrentAppProfile();
    setProfile(appProfile);
  }

  async function logout() {
    await signOut();
    setSession(null);
    setProfile(null);
  }

  useEffect(() => {
    async function initializeAuth() {
      const { data } = await supabase.auth.getSession();
      setSession(data.session);

      if (data.session) {
        await refreshProfile();
      }

      setLoading(false);
    }

    initializeAuth();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setSession(session);

      if (session) {
        await refreshProfile();
      } else {
        setProfile(null);
      }

      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        session,
        profile,
        loading,
        refreshProfile,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
