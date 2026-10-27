import { useAuth } from "@/src/auth";

// Pro = paid licence or the 14-day free Pro trial, while not expired.
// An expired trial drops to the Free plan (app keeps working, Pro features lock).
export const isExpired = (o: any) => !!o?.expires_at && Date.parse(o.expires_at) < Date.now();
export const isPro = (o: any) => !!o && o.status === "ACTIVE" && !isExpired(o) && ["TRIAL", "LICENSE"].includes(o.plan);
export const daysLeft = (o: any) => (o?.expires_at ? Math.ceil((Date.parse(o.expires_at) - Date.now()) / 86400000) : 0);
export const planLabel = (o: any) => (o?.plan === "LICENSE" ? (isExpired(o) ? "منتهي" : "Pro") : isExpired(o) ? "مجاني" : "Pro تجريبي");

export function usePro() {
  const { user } = useAuth();
  const org = user?.org;
  const trial = org?.plan === "TRIAL";
  return { org, pro: isPro(org), trial: trial && !isExpired(org), free: trial && isExpired(org), daysLeft: daysLeft(org), isOwner: user?.role === "OWNER" };
}

// Login screen trial offer -> activation screen leads with the trial form.
export const TRIAL_INTENT_KEY = "trial_intent";
