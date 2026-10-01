export type BillingPresentationInput = {
  status: string;
  first_billing_at: string | null;
  paid_until: string | null;
  trial_days: number;
};

export type BillingPresentation = {
  canStartCheckout: boolean;
  canCancel: boolean;
  statusLabel: string;
  scheduleKind: "first_billing" | "renewal" | "unconfirmed";
  scheduleAt: string | null;
  scheduleMessage: string;
  disclosure: string;
};

const checkoutAvailable = new Set(["trial_pending", "trial", "trial_expired", "canceled", "incomplete_expired"]);
const cancellable = new Set(["trialing", "active", "past_due", "unpaid", "paused"]);
const labels: Record<string, string> = {
  trial: "試用中（カード未登録）",
  trialing: "カード登録済み・無料期間中",
  trial_pending: "カード登録待ち",
  trial_expired: "試用終了・カード未登録",
  active: "有料利用中",
  past_due: "支払い確認が必要",
  canceled: "解約済み",
  unpaid: "支払い未完了",
  incomplete: "契約手続き未完了",
  incomplete_expired: "契約手続き期限切れ",
  paused: "契約一時停止中",
};

export function getBillingPresentation(data: BillingPresentationInput): BillingPresentation {
  const base = {
    canStartCheckout: checkoutAvailable.has(data.status),
    canCancel: cancellable.has(data.status),
    statusLabel: labels[data.status] ?? "状態を確認してください",
  };
  const trialDays = Number.isFinite(data.trial_days) && data.trial_days > 0 ? data.trial_days : 7;

  if (data.status === "trialing" && data.first_billing_at) {
    return {
      ...base,
      scheduleKind: "first_billing",
      scheduleAt: data.first_billing_at,
      scheduleMessage: "カード登録と無料期間が開始されています。",
      disclosure: `カード登録済みです。${trialDays}日間の無料期間終了後に月額19,800円（税込）が自動課金され、以後1か月ごとに自動更新されます。`,
    };
  }

  if (data.status === "trialing") {
    return {
      ...base,
      scheduleKind: "unconfirmed",
      scheduleAt: null,
      scheduleMessage: "カード登録済みですが、初回課金日時を確認できません。契約状態を再読み込みしてください。",
      disclosure: "カード登録済みです。初回課金日時を確認できるまで、確定日時として案内しません。",
    };
  }

  if (data.status === "active" && data.paid_until) {
    return {
      ...base,
      scheduleKind: "renewal",
      scheduleAt: data.paid_until,
      scheduleMessage: "有料契約が有効です。",
      disclosure: "月額19,800円（税込）の有料契約です。期間末までに解約しない場合、1か月ごとに自動更新されます。",
    };
  }

  if (data.status === "active") {
    return {
      ...base,
      scheduleKind: "unconfirmed",
      scheduleAt: null,
      scheduleMessage: "有料契約は有効ですが、次回更新日時を確認できません。契約状態を再読み込みしてください。",
      disclosure: "月額19,800円（税込）の有料契約です。次回更新日時を確認できるまで、確定日時として案内しません。",
    };
  }

  if (["past_due", "unpaid"].includes(data.status)) {
    return {
      ...base,
      scheduleKind: "unconfirmed",
      scheduleAt: null,
      scheduleMessage: "支払い状況の確認が必要なため、次回課金日時は確定表示していません。",
      disclosure: "支払い状態を確認してください。状態が解消するまで新しい申込みや確定日時の案内は行いません。",
    };
  }

  if (data.status === "paused") {
    return {
      ...base,
      scheduleKind: "unconfirmed",
      scheduleAt: null,
      scheduleMessage: "契約は一時停止中です。課金再開日時は確定していません。",
      disclosure: "契約状態を確認してください。再開日時が確定するまで課金予定日は表示しません。",
    };
  }

  if (data.status === "incomplete") {
    return {
      ...base,
      scheduleKind: "unconfirmed",
      scheduleAt: null,
      scheduleMessage: "申込み手続きは完了していません。課金日時はまだ確定していません。",
      disclosure: "カード登録と契約状態が確定するまで請求は開始されません。申込み状態を確認してください。",
    };
  }

  if (checkoutAvailable.has(data.status)) {
    return {
      ...base,
      scheduleKind: "unconfirmed",
      scheduleAt: null,
      scheduleMessage: `カード登録後、${trialDays}日間の無料期間終了時に初回課金されます。申込み完了前のため、課金日時はまだ確定していません。`,
      disclosure: `本日の請求額は0円です。カード登録後${trialDays}日間は無料です。無料期間中に解約しない場合、月額19,800円（税込）が自動課金され、以後1か月ごとに自動更新されます。`,
    };
  }

  return {
    ...base,
    scheduleKind: "unconfirmed",
    scheduleAt: null,
    scheduleMessage: "契約状態を確認できないため、課金日時は表示していません。",
    disclosure: "契約状態を再読み込みし、確認できるまで申込みや解約操作を行わないでください。",
  };
}
