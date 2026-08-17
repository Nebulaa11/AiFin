import { createContext, useContext } from "react";

type GoogleConfigContextValue = {
  clientId: string;
  devAuthEnabled: boolean;
};

export const GoogleConfigContext = createContext<GoogleConfigContextValue>({
  clientId: "",
  devAuthEnabled: false,
});

export function useGoogleConfig() {
  return useContext(GoogleConfigContext);
}
