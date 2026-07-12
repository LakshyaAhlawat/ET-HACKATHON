const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiPost<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status} ${await res.text()}`);
  }
  return res.json() as Promise<TResponse>;
}
