const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

function apiUrl(path: string) {
  if (!apiBaseUrl) {
    return path;
  }
  return new URL(path, apiBaseUrl).toString();
}

async function readJson<TResponse>(response: Response): Promise<TResponse> {
  const text = await response.text();
  if (!text) {
    return {} as TResponse;
  }

  try {
    return JSON.parse(text) as TResponse;
  } catch {
    throw new Error(`The API returned an unexpected response with status ${response.status}.`);
  }
}

export async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
  let response: Response;

  try {
    response = await fetch(apiUrl(path), {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });
  } catch {
    throw new Error("The API is not reachable. Start the Azure Functions API locally or check the deployed API connection.");
  }

  const data = await readJson<TResponse>(response);
  if (!response.ok && response.status !== 207) {
    const maybeError = data as { detail?: string; error?: string };
    throw new Error(maybeError.error ?? maybeError.detail ?? `Request failed with status ${response.status}`);
  }
  return data;
}

export async function getJson<TResponse>(path: string): Promise<TResponse> {
  let response: Response;

  try {
    response = await fetch(apiUrl(path));
  } catch {
    throw new Error("The API is not reachable. Start the Azure Functions API locally or check the deployed API connection.");
  }

  const data = await readJson<TResponse>(response);
  if (!response.ok) {
    const maybeError = data as { detail?: string; error?: string };
    throw new Error(maybeError.error ?? maybeError.detail ?? `Request failed with status ${response.status}`);
  }
  return data;
}

export async function getCurrentUser(): Promise<{ clientPrincipal: { userDetails: string } | null }> {
  try {
    const response = await fetch("/.auth/me");
    if (!response.ok) {
      return { clientPrincipal: null };
    }
    return readJson(response);
  } catch {
    return { clientPrincipal: null };
  }
}
