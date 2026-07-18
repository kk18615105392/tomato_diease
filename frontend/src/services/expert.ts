export type ExpertDiagnosisContext = {
  disease_name?: string;
  dsi?: number;
  severity_level?: string;
  confidence?: number;
  mode?: string;
};

export type ChatMessage = {
  id: string;
  role: "system" | "user" | "assistant";
  content: string;
  time: string;
};

export async function streamExpertChat(
  message: string,
  diagnosis: ExpertDiagnosisContext,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (err: Error) => void,
): Promise<void> {
  try {
    const res = await fetch("/api/chat_expert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, diagnosis }),
    });

    if (!res.ok) throw new Error(`请求失败 (${res.status})`);
    if (!res.body) throw new Error("响应体为空");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6).trim();
        if (payload === "[DONE]") {
          onDone();
          return;
        }
        try {
          const parsed = JSON.parse(payload) as { content?: string };
          if (parsed.content) onChunk(parsed.content);
        } catch {
          /* ignore malformed chunks */
        }
      }
    }
    onDone();
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}
