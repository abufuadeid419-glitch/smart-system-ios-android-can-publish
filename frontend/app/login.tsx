import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useEffect, useRef, useState } from "react";
import { Pressable, TextInput, useWindowDimensions, View } from "react-native";
import { useReanimatedKeyboardAnimation } from "react-native-keyboard-controller";
import Animated, { interpolate, useAnimatedStyle } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "@/src/auth";
import { KeyboardScreen } from "@/src/components/KeyboardScreen";
import { DeviceConflictSheet } from "@/src/components/DeviceConflictSheet";
import { isValidCallingCode } from "@/src/phone";
import { fonts, makeStyles, radius, spacing, useTheme } from "@/src/theme";
import { Badge, Btn, Field, Ionicons, T } from "@/src/ui";
import { storage } from "@/src/utils/storage";
import { TRIAL_INTENT_KEY } from "@/src/pro";

// Free Pro trial offer for new owners: tapping it remembers the intent (the activation screen then
// leads with the trial form) and focuses the phone field so sign-up starts right away.
function TrialOffer({ picked, onPick }: { picked: boolean; onPick: () => void }) {
  const styles = useStyles();
  const { colors } = useTheme();
  return (
    <View style={styles.trial} testID="login-trial-offer">
      <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}>
        <Ionicons name="diamond-outline" size={20} color={colors.brandPrimary} />
        <T v="label" style={{ flex: 1, fontSize: 16 }}>جرّب Pro مجاناً لمدة 14 يوماً</T>
        <Badge text="مجاناً" tone="pro" />
      </View>
      <T v="caption">للمالكين الجدد: كل ميزات Pro بدون بطاقة دفع. سجّل برقمك ثم أدخل اسم مؤسستك وابدأ فوراً.</T>
      {picked ? (
        <View testID="login-trial-picked" style={{ flexDirection: "row", alignItems: "center", gap: spacing.xs }}>
          <Ionicons name="checkmark-circle" size={18} color={colors.success} />
          <T v="caption" color="success" style={{ flex: 1 }}>تم اختيار التجربة المجانية — أدخل رقمك بالأسفل للمتابعة</T>
        </View>
      ) : (
        <Btn testID="login-start-trial-button" small variant="secondary" icon="rocket-outline" title="ابدأ تجربتك المجانية" onPress={onPick} />
      )}
    </View>
  );
}

const HERO =
  "https://images.unsplash.com/photo-1587293852726-70cdb56c2866?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200";

export default function Login() {
  return <PhoneAuth />;
}

// Hero collapses smoothly into a compact title bar while the keyboard is open, so the form and CTA
// keep their full size instead of being squished.
function Hero() {
  const insets = useSafeAreaInsets();
  const { height: winH } = useWindowDimensions();
  const styles = useStyles();
  const { colors } = useTheme();
  const { progress } = useReanimatedKeyboardAnimation();
  const full = Math.min(winH * 0.38, 340);
  const compact = insets.top + 72;
  const box = useAnimatedStyle(() => ({ height: interpolate(progress.value, [0, 1], [full, compact]) }));
  const fade = useAnimatedStyle(() => ({ opacity: interpolate(progress.value, [0, 0.5], [1, 0]), transform: [{ scale: interpolate(progress.value, [0, 1], [1, 0.9]) }] }));
  return (
    <Animated.View style={[styles.hero, box]} testID="login-hero">
      <Image source={{ uri: HERO }} style={StyleFill} contentFit="cover" />
      <LinearGradient colors={["rgba(25,28,27,0.15)", "rgba(25,28,27,0.85)"]} style={StyleFill} />
      <View style={{ paddingTop: insets.top + spacing.md, paddingHorizontal: spacing.xl, flex: 1, justifyContent: "flex-end", paddingBottom: spacing.lg }}>
        <Animated.View style={[styles.logo, fade]}>
          <Ionicons name="business" size={30} color={colors.onBrandPrimary} />
        </Animated.View>
        <T v="display" color="onBrandPrimary">النظام الذكي</T>
        <Animated.View style={fade}>
          <T color="onBrandPrimary" style={{ opacity: 0.9 }}>نظام متكامل لإدارة المبيعات والتوزيع</T>
        </Animated.View>
      </View>
    </Animated.View>
  );
}

const StyleFill = { position: "absolute" as const, top: 0, left: 0, right: 0, bottom: 0 };

function Features() {
  const styles = useStyles();
  const { colors } = useTheme();
  const features: { icon: any; text: string }[] = [
    { icon: "cube-outline", text: "إدارة المخزون والمنتجات" },
    { icon: "receipt-outline", text: "فواتير المبيعات والتحصيل" },
    { icon: "people-outline", text: "الموزعون والمحاسبون والعملاء" },
  ];
  return (
    <View style={{ gap: spacing.md }}>
      {features.map((f) => (
        <View key={f.text} style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
          <View style={styles.fIcon}>
            <Ionicons name={f.icon} size={20} color={colors.brandPrimary} />
          </View>
          <T v="label">{f.text}</T>
        </View>
      ))}
    </View>
  );
}

const DEFAULT_CC = "+963";
const RESEND_SECONDS = 60;

// Password input with a show/hide toggle.
function PasswordField({ testID, label, value, onChangeText, onSubmitEditing, autoFocus }: { testID: string; label: string; value: string; onChangeText: (t: string) => void; onSubmitEditing?: () => void; autoFocus?: boolean }) {
  const { colors } = useTheme();
  const [show, setShow] = useState(false);
  return (
    <View style={{ gap: spacing.xs }}>
      <T v="label" color="onSurfaceSecondary">{label}</T>
      <View style={[inputStyle(colors), { flexDirection: "row", alignItems: "center", paddingHorizontal: 0 }]}>
        <TextInput
          testID={testID}
          value={value}
          onChangeText={onChangeText}
          secureTextEntry={!show}
          autoCapitalize="none"
          autoCorrect={false}
          autoComplete="password"
          textContentType="password"
          autoFocus={autoFocus}
          returnKeyType="done"
          onSubmitEditing={onSubmitEditing}
          placeholder="••••••••"
          placeholderTextColor={colors.muted}
          style={{ flex: 1, minHeight: 50, paddingHorizontal: spacing.md, fontFamily: fonts.regular, fontSize: 17, color: colors.onSurface, textAlign: "right" }}
        />
        <Pressable testID={`${testID}-toggle`} onPress={() => setShow(!show)} hitSlop={8} style={{ width: 48, height: 50, alignItems: "center", justifyContent: "center" }}>
          <Ionicons name={show ? "eye-off-outline" : "eye-outline"} size={20} color={colors.muted} />
        </Pressable>
      </View>
    </View>
  );
}

const pwRules = (p: string) => [
  { ok: p.length >= 8, text: "8 أحرف على الأقل" },
  { ok: /\p{L}/u.test(p), text: "تحتوي على حرف" },
  { ok: /\d/.test(p), text: "تحتوي على رقم" },
];

// Phone → (password | SMS code → set password) → name (first login only).
// Each step: scrollable form + sticky footer (error + CTA).
function PhoneAuth() {
  const { user, busy, error, requestOtp, verifyOtp, startLogin, loginPassword, setPassword, saveName, logout } = useAuth();
  const { colors } = useTheme();
  const styles = useStyles();
  const [cc, setCc] = useState(DEFAULT_CC);
  const [local, setLocal] = useState("");
  const [step, setStep] = useState<"phone" | "password" | "code">("phone");
  const [target, setTarget] = useState("");
  const [code, setCode] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [name, setName] = useState("");
  const [wait, setWait] = useState(0);
  const [resetting, setResetting] = useState(false);
  const [trialPicked, setTrialPicked] = useState(false);
  const phoneRef = useRef<any>(null);
  const pickTrial = () => {
    setTrialPicked(true);
    storage.setItem(TRIAL_INTENT_KEY, true);
    phoneRef.current?.focus();
  };

  useEffect(() => {
    if (wait <= 0) return;
    const t = setTimeout(() => setWait(wait - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

  const ccDigits = cc.replace(/\D/g, "");
  // Reject fake/unassigned country codes (e.g. "+123") up front so we never waste an SMS.
  const ccValid = isValidCallingCode(ccDigits);
  // Accept "0947…", "947…", "963947…" or "00963947…" in the local field.
  const localDigits = local.replace(/\D/g, "").replace(/^00/, "").replace(new RegExp(`^${ccDigits}(?=\\d{7,})`), "").replace(/^0+/, "");
  const phone = `+${ccDigits}${localDigits}`;
  const localValid = localDigits.length >= 6;

  const toCode = () => {
    setStep("code");
    setCode("");
    setWait(RESEND_SECONDS);
  };
  const next = async () => {
    if (!ccValid || !localValid || busy) return;
    const m = await startLogin(phone);
    if (!m) return;
    setTarget(phone);
    setPw("");
    if (m === "password") setStep("password");
    else toCode();
  };
  const resend = async () => {
    if (await requestOtp(target)) toCode();
  };
  const forgot = async () => {
    setResetting(true);
    if (await requestOtp(target)) toCode();
    else setResetting(false);
  };
  const back = () => {
    setStep("phone");
    setResetting(false);
  };

  const err = !!error && <T testID="login-error" color="error" style={{ textAlign: "center" }}>{error}</T>;
  const screen = (testID: string, body: React.ReactNode, footer: React.ReactNode) => (
    <KeyboardScreen testID="login-screen" header={<Hero />} footer={footer} contentContainerStyle={styles.body}>
      <View style={{ gap: spacing.md }} testID={testID}>{body}</View>
    </KeyboardScreen>
  );

  // Signed in by SMS code without a password yet (or resetting it): choose one now.
  if (user && user.has_password === false) {
    const rules = pwRules(pw);
    const valid = rules.every((r) => r.ok) && pw === pw2;
    const submit = async () => {
      if (!valid) return;
      if (await setPassword(pw)) {
        setResetting(false);
        setPw("");
        setPw2("");
      }
    };
    return screen(
      "set-password-step",
      <>
        <T v="h2">عيّن كلمة المرور لحسابك</T>
        <T v="caption">في المرات القادمة ستدخل برقم هاتفك وكلمة المرور هذه بدون رمز SMS.</T>
        <PasswordField testID="login-new-password-input" label="كلمة المرور" value={pw} onChangeText={setPw} autoFocus />
        <PasswordField testID="login-confirm-password-input" label="تأكيد كلمة المرور" value={pw2} onChangeText={setPw2} onSubmitEditing={submit} />
        <View style={{ gap: spacing.xs }} testID="login-password-rules">
          {rules.map((r) => (
            <View key={r.text} style={{ flexDirection: "row", alignItems: "center", gap: spacing.xs }}>
              <Ionicons name={r.ok ? "checkmark-circle" : "ellipse-outline"} size={16} color={r.ok ? colors.success : colors.muted} />
              <T v="caption" color={r.ok ? "success" : undefined}>{r.text}</T>
            </View>
          ))}
          {pw2.length > 0 && pw !== pw2 && <T testID="login-password-mismatch" v="caption" color="error">كلمتا المرور غير متطابقتين</T>}
        </View>
      </>,
      <>
        {err}
        <Btn testID="login-set-password-submit" title="حفظ كلمة المرور" icon="lock-closed-outline" loading={busy} disabled={!valid} onPress={submit} />
        <Btn testID="login-password-logout" variant="ghost" small title="تسجيل الخروج" onPress={logout} />
      </>,
    );
  }

  if (user && !user.name) {
    return screen(
      "name-step",
      <>
        <T v="h2">مرحباً بك! ما اسمك؟</T>
        <Field testID="login-name-input" label="الاسم الكامل" value={name} onChangeText={setName} placeholder="مثال: أحمد محمد" autoFocus returnKeyType="done" onSubmitEditing={() => saveName(name)} />
      </>,
      <>
        {err}
        <Btn testID="login-name-submit" title="متابعة" icon="arrow-back" loading={busy} disabled={name.trim().length < 2} onPress={() => saveName(name)} />
        <Btn testID="login-name-logout" variant="ghost" small title="تسجيل الخروج" onPress={logout} />
      </>,
    );
  }

  const phoneLabel = <T v="label" style={{ writingDirection: "ltr" }}>{target}</T>;

  if (step === "password") {
    return screen(
      "password-step",
      <>
        <T v="h2">أدخل كلمة المرور</T>
        <T v="caption">الدخول إلى الحساب {phoneLabel}</T>
        <PasswordField testID="login-password-input" label="كلمة المرور" value={pw} onChangeText={setPw} autoFocus onSubmitEditing={() => pw && loginPassword(target, pw)} />
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
          <Btn testID="login-change-phone" variant="ghost" small title="تغيير الرقم" onPress={back} />
          <Btn testID="login-forgot-password" variant="ghost" small title="نسيت كلمة المرور؟" disabled={busy} onPress={forgot} />
        </View>
      </>,
      <>
        {err}
        <Btn testID="login-password-submit" title="دخول" icon="log-in-outline" loading={busy} disabled={!pw} onPress={() => loginPassword(target, pw)} />
        <DeviceConflictSheet />
      </>,
    );
  }

  if (step === "code") {
    return screen(
      "code-step",
      <>
        <T v="h2">{resetting ? "تأكيد استعادة الحساب" : "أدخل رمز التحقق"}</T>
        <View testID="login-sent-via" style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}>
          <Ionicons name="chatbubble-ellipses-outline" size={18} color={colors.brandPrimary} />
          <T v="caption" style={{ flex: 1 }}>أرسلنا رمزاً مكوناً من 6 أرقام عبر رسالة SMS إلى {phoneLabel}</T>
        </View>
        <Field
          testID="login-code-input"
          label="رمز التحقق"
          value={code}
          onChangeText={(t) => setCode(t.replace(/\D/g, "").slice(0, 6))}
          keyboardType="number-pad"
          textContentType="oneTimeCode"
          autoComplete="sms-otp"
          maxLength={6}
          autoFocus
          placeholder="••••••"
          style={{ textAlign: "center", letterSpacing: 8, fontSize: 22 }}
          onSubmitEditing={() => code.length === 6 && verifyOtp(target, code, false, resetting)}
        />
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
          <Btn testID="login-change-phone" variant="ghost" small title="تغيير الرقم" onPress={back} />
          <Btn testID="login-resend-button" variant="ghost" small title={wait > 0 ? `إعادة الإرسال خلال ${wait} ث` : "إعادة إرسال الرمز"} disabled={wait > 0 || busy} onPress={resend} />
        </View>
      </>,
      <>
        {err}
        <Btn testID="login-verify-button" title="تحقق ومتابعة" icon="checkmark" loading={busy} disabled={code.length !== 6} onPress={() => verifyOtp(target, code, false, resetting)} />
        <DeviceConflictSheet />
      </>,
    );
  }

  return screen(
    "phone-step",
    <>
      <Features />
      <TrialOffer picked={trialPicked} onPick={pickTrial} />
      <View style={{ gap: spacing.sm, marginTop: spacing.md }}>
        <T v="label" color="onSurfaceSecondary">رقم الهاتف</T>
        <View style={{ flexDirection: "row-reverse", gap: spacing.sm }}>
          <TextInput
            testID="login-country-code-input"
            value={cc}
            onChangeText={(t) => setCc("+" + t.replace(/\D/g, "").slice(0, 4))}
            keyboardType="phone-pad"
            style={[inputStyle(colors), { width: 84, textAlign: "center" }]}
          />
          <TextInput
            testID="login-phone-input"
            ref={phoneRef}
            value={local}
            onChangeText={(t) => setLocal(t.replace(/[^\d]/g, "").slice(0, 12))}
            keyboardType="phone-pad"
            textContentType="telephoneNumber"
            autoComplete="tel"
            placeholder="9XXXXXXXX"
            placeholderTextColor={colors.muted}
            returnKeyType="done"
            onSubmitEditing={next}
            style={[inputStyle(colors), { flex: 1, textAlign: "left", writingDirection: "ltr" }]}
          />
        </View>
        {ccDigits.length > 0 && !ccValid && (
          <T testID="login-cc-error" v="caption" color="error">رمز الدولة غير صحيح، تحقق منه قبل الإرسال</T>
        )}
      </View>
    </>,
    <>
      {err}
      <Btn testID="login-continue-button" title="متابعة" icon="arrow-back" loading={busy} disabled={!ccValid || !localValid} onPress={next} />
      <T v="caption" style={{ textAlign: "center" }}>بالمتابعة أنت توافق على شروط الاستخدام وسياسة الخصوصية</T>
    </>,
  );
}

const inputStyle = (c: any) => ({
  minHeight: 50,
  borderRadius: radius.md,
  borderWidth: 1,
  borderColor: c.border,
  backgroundColor: c.surfaceSecondary,
  paddingHorizontal: spacing.md,
  fontFamily: fonts.regular,
  fontSize: 17,
  color: c.onSurface,
});

const useStyles = makeStyles((c) => ({
  hero: { overflow: "hidden", backgroundColor: c.surfaceInverse },
  logo: { width: 56, height: 56, borderRadius: radius.md, backgroundColor: c.brandPrimary, alignItems: "center", justifyContent: "center", marginBottom: spacing.md },
  body: { padding: spacing.xl, gap: spacing.xl },
  trial: { gap: spacing.sm, padding: spacing.md, borderRadius: radius.md, borderWidth: 1, borderColor: c.brandPrimary, backgroundColor: c.brandTertiary },
  fIcon: { width: 40, height: 40, borderRadius: radius.md, backgroundColor: c.brandTertiary, alignItems: "center", justifyContent: "center" },
}));
