import { NextResponse } from "next/server";

function schemeApiBaseUrl(): string {
  const configured = process.env.SCHEME_API_BASE_URL?.trim();
  const base = configured && configured.length > 0 ? configured : "http://127.0.0.1:8001";
  return base.replace(/\/$/, "");
}

/** Forwards a citizen profile to the existing predictor. Does not score eligibility. */
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Profile must be valid JSON." }, { status: 400 });
  }

  let response: Response;
  try {
    response = await fetch(`${schemeApiBaseUrl()}/api/v1/recommend`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "The government scheme predictor could not be reached." },
      { status: 503 },
    );
  }

  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") ?? "application/json",
    },
  });
}
