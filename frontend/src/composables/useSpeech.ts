import { ref } from "vue";
import { ElMessage } from "element-plus";

export function useSpeech(onResult: (text: string) => void) {
  const listening = ref(false);
  const supported = ref(
    typeof window !== "undefined" &&
      ("SpeechRecognition" in window || "webkitSpeechRecognition" in window),
  );

  let recognition: SpeechRecognition | null = null;

  function startListen() {
    if (!supported.value) {
      ElMessage.warning("当前浏览器不支持语音识别，请使用 Chrome");
      return;
    }

    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = "zh-CN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      listening.value = true;
    };
    recognition.onresult = (e: SpeechRecognitionEvent) => {
      const text = e.results[0]?.[0]?.transcript ?? "";
      if (text) onResult(text);
    };
    recognition.onerror = () => {
      ElMessage.error("语音识别失败，请重试");
      listening.value = false;
    };
    recognition.onend = () => {
      listening.value = false;
    };
    recognition.start();
  }

  function stopListen() {
    recognition?.stop();
    listening.value = false;
  }

  return { listening, supported, startListen, stopListen };
}

declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
