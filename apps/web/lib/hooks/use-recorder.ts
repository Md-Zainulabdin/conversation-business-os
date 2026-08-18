import { useCallback, useEffect, useRef, useState } from "react";

const RECORDING_MIME_TYPE = "audio/webm";
const MAX_RECORDING_SECONDS = 60;

export function useRecorder() {
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setElapsed(0);
  }, []);

  const cleanup = useCallback(() => {
    mediaRecorderRef.current?.stream.getTracks().forEach((track) => track.stop());
    streamRef.current?.getTracks().forEach((track) => track.stop());
    mediaRecorderRef.current = null;
    streamRef.current = null;
    chunksRef.current = [];
    stopTimer();
    setRecording(false);
  }, [stopTimer]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  const start = useCallback(async (): Promise<Blob | null> => {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Audio recording is not supported in this browser.");
      return null;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Microphone permission was denied. Allow access to record.");
      return null;
    }

    let mimeType = "audio/webm";
    if (typeof MediaRecorder !== "undefined" && !MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = "audio/mp4";
    }
    if (typeof MediaRecorder === "undefined") {
      stream.getTracks().forEach((track) => track.stop());
      setError("Audio recording is not supported in this browser.");
      return null;
    }

    streamRef.current = stream;
    chunksRef.current = [];

    return await new Promise<Blob | null>((resolve) => {
      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported(mimeType) ? mimeType : undefined,
      });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || RECORDING_MIME_TYPE,
        });
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        mediaRecorderRef.current = null;
        stopTimer();
        setRecording(false);
        resolve(blob.size > 0 ? blob : null);
      };

      recorder.onerror = () => {
        stream.getTracks().forEach((track) => track.stop());
        mediaRecorderRef.current = null;
        stopTimer();
        setRecording(false);
        setError("Recording failed. Please try again.");
        resolve(null);
      };

      recorder.start();
      setRecording(true);
      const startedAt = Date.now();
      timerRef.current = window.setInterval(() => {
        const elapsedSeconds = Math.floor((Date.now() - startedAt) / 1000);
        setElapsed(elapsedSeconds);
        if (elapsedSeconds >= MAX_RECORDING_SECONDS) {
          recorder.stop();
        }
      }, 250);
    });
  }, [stopTimer]);

  const stop = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  return { recording, elapsed, error, start, stop };
}