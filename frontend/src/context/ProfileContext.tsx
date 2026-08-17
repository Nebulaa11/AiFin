import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api } from "../api/client";
import { useAuth } from "./AuthContext";
import type { AnalyzeResponse, UserProfile } from "../types";
import { defaultProfile } from "../types";

type ProfileContextValue = {
  profile: UserProfile;
  setProfile: (p: UserProfile | ((prev: UserProfile) => UserProfile)) => void;
  analysis: AnalyzeResponse | null;
  setAnalysis: (a: AnalyzeResponse | null) => void;
  profileLoading: boolean;
  analyzing: boolean;
  saveProfile: () => Promise<void>;
  runAnalyze: () => Promise<AnalyzeResponse | null>;
  updateField: <K extends keyof UserProfile>(key: K, value: UserProfile[K]) => void;
};

const ProfileContext = createContext<ProfileContextValue | null>(null);

export function ProfileProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfile>(defaultProfile());
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>();

  const loadProfile = useCallback(async () => {
    if (!user) return;
    setProfileLoading(true);
    try {
      const { data } = await api.get<{ profile: UserProfile; last_analysis: AnalyzeResponse | null }>(
        "/user/profile"
      );
      setProfile(data.profile);
      if (data.last_analysis) setAnalysis(data.last_analysis);
    } catch {
      setProfile(defaultProfile());
    } finally {
      setProfileLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) loadProfile();
    else {
      setProfile(defaultProfile());
      setAnalysis(null);
    }
  }, [user, loadProfile]);

  const saveProfile = useCallback(async () => {
    if (!user) return;
    await api.put("/user/profile", { profile, last_analysis: analysis });
  }, [user, profile, analysis]);

  useEffect(() => {
    if (!user) return;
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      api.put("/user/profile", { profile, last_analysis: analysis }).catch(() => {});
    }, 1200);
    return () => clearTimeout(saveTimer.current);
  }, [user, profile, analysis]);

  const runAnalyze = async () => {
    setAnalyzing(true);
    try {
      const { data } = await api.post<AnalyzeResponse>("/analyze", profile);
      setAnalysis(data);
      if (user) {
        await api.put("/user/profile", { profile, last_analysis: data });
      }
      return data;
    } finally {
      setAnalyzing(false);
    }
  };

  const updateField = <K extends keyof UserProfile>(key: K, value: UserProfile[K]) => {
    setProfile((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <ProfileContext.Provider
      value={{
        profile,
        setProfile,
        analysis,
        setAnalysis,
        profileLoading,
        analyzing,
        saveProfile,
        runAnalyze,
        updateField,
      }}
    >
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile() {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error("useProfile must be used within ProfileProvider");
  return ctx;
}
