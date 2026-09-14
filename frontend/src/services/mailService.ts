import {
  apiDelete,
  apiGet,
} from "@/lib/api";

export type GmailConnection = {
  id: string;
  email: string;
  status: string;
  created_at: string;
};

export type GmailStatusResponse = {
  connected: boolean;
  connection: GmailConnection | null;
  sync: {mode:string;last_page_at:string;last_successful_sync:string|null}|null;
  last_run: {status:string;started_at:string;finished_at:string|null;detected_count:number;error_code:string|null}|null;
  message: string;
};

export type GmailAuthUrlResponse = {
  auth_url: string;
  state: string;
  company_id: string;
  scopes: string[];
};

export type GmailDisconnectResponse = {
  disconnected: boolean;
  message: string;
};

export async function getGmailStatus() {
  return apiGet<GmailStatusResponse>(
    "/gmail/status"
  );
}

export async function getGmailAuthUrl() {
  return apiGet<GmailAuthUrlResponse>(
    "/gmail/auth-url"
  );
}

export async function disconnectGmail() {
  return apiDelete<GmailDisconnectResponse>(
    "/gmail/disconnect"
  );
}
