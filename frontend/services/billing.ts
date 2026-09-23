/**
 * RevenueCat client SDK wrapper — the piece that actually starts a real
 * App Store / Play Store purchase from the paywall screen.
 *
 * UNVERIFIED AGAINST A LIVE REVENUECAT ACCOUNT OR A REAL DEVICE BUILD. This
 * follows react-native-purchases' documented v8 API (Purchases.configure,
 * getOfferings, purchasePackage, restorePurchases), but there is no
 * RevenueCat project or App Store Connect/Play Console product configured in
 * this environment, and — more importantly — `react-native-purchases` is a
 * native module: it cannot run in Expo Go and this sandbox cannot build or
 * launch a native binary. It has not been exercised end-to-end.
 *
 * Before this goes live: create the RevenueCat project (see
 * backend/app/services/revenuecat.py for the server side), set
 * EXPO_PUBLIC_REVENUECAT_IOS_KEY / EXPO_PUBLIC_REVENUECAT_ANDROID_KEY (the
 * platform *public* SDK keys — never the secret key used server-side), build
 * a custom EAS dev client (`eas build --profile development`), and confirm
 * a real purchase completes and `syncSubscription()` reflects it.
 */
import { Platform } from "react-native";
import Purchases, { type CustomerInfo, type PurchasesOffering, type PurchasesPackage } from "react-native-purchases";

import { apiRequest } from "./api";
import type { User } from "./types";

const IOS_API_KEY = process.env.EXPO_PUBLIC_REVENUECAT_IOS_KEY ?? "";
const ANDROID_API_KEY = process.env.EXPO_PUBLIC_REVENUECAT_ANDROID_KEY ?? "";

let configured = false;
let unavailableReason: string | null = null;

/** True once native purchases can actually be attempted. False on web
 * (no in-app-purchase concept), when no platform API key is set, or when
 * the native module failed to initialize (e.g. running in Expo Go instead
 * of a custom dev client). The paywall UI should check this before
 * rendering a "buy" button. */
export function isAvailable(): boolean {
  return configured;
}

export function unavailableMessage(): string | null {
  return unavailableReason;
}

export async function configureBilling(appUserId: string): Promise<void> {
  if (Platform.OS === "web") {
    unavailableReason = "Purchases aren't available on web — use the iOS or Android app.";
    return;
  }
  const apiKey = Platform.OS === "ios" ? IOS_API_KEY : ANDROID_API_KEY;
  if (!apiKey) {
    unavailableReason = "Subscriptions aren't configured yet for this build.";
    if (__DEV__) console.warn("[billing] No RevenueCat API key set for this platform — purchases disabled.");
    return;
  }
  try {
    Purchases.configure({ apiKey, appUserID: appUserId });
    configured = true;
    unavailableReason = null;
  } catch (error) {
    // Expected in Expo Go, where the native module isn't linked.
    configured = false;
    unavailableReason = "Purchases aren't available in this build.";
    if (__DEV__) console.warn("[billing] RevenueCat configure failed (expected outside a custom dev client):", error);
  }
}

export async function logOutBilling(): Promise<void> {
  if (!configured) return;
  try {
    await Purchases.logOut();
  } catch {
    // best-effort — local sign-out should never be blocked by this
  } finally {
    configured = false;
  }
}

export async function getCurrentOffering(): Promise<PurchasesOffering | null> {
  if (!configured) return null;
  const offerings = await Purchases.getOfferings();
  return offerings.current;
}

export async function purchasePackage(pkg: PurchasesPackage): Promise<CustomerInfo> {
  const { customerInfo } = await Purchases.purchasePackage(pkg);
  return customerInfo;
}

export async function restorePurchases(): Promise<CustomerInfo> {
  return Purchases.restorePurchases();
}

/** Call right after a purchase or restore completes so our own entitlement
 * record reflects reality immediately, without waiting for the RevenueCat
 * webhook. The server never trusts anything about the purchase beyond "go
 * check RevenueCat again" — see POST /subscriptions/sync. */
export async function syncSubscription(): Promise<User> {
  return apiRequest<User>("/subscriptions/sync", { method: "POST" });
}
