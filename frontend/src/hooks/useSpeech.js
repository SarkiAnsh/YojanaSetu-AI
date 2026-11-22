/**
 * useSpeech.js — Custom hook for voice input (speech-to-text)
 * and voice output (text-to-speech).
 *
 * Uses the browser's built-in Web Speech API — no extra libraries needed.
 * Works in Chrome and Edge. Limited support in Firefox.
 *
 * Usage:
 *   const { isListening, startListening, speak, supported } = useSpeech(lang)
 */

import { useState, useCallback, useEffect, useRef } from 'react'

export function useSpeech(lang = 'en') {
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef(null)
  const startingRef = useRef(false)
  const startRequestRef = useRef(0)
  const errorHandlerRef = useRef(null)

  const SpeechRecognition = typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null
  const supported = !!SpeechRecognition

  /**
   * Start listening for voice input.
   * @param {Function} onResult - Called with the transcript string when done
   */
  const startListening = useCallback(async (onResult, onError) => {
    const reportError = (english, hindi) => onError?.(lang === 'hi' ? hindi : english)

    if (!supported) {
      reportError(
        'Voice input is not supported in this browser. Please use Chrome or Edge.',
        'यह ब्राउज़र वॉइस इनपुट को सपोर्ट नहीं करता। कृपया Chrome या Edge उपयोग करें।'
      )
      return
    }

    if (recognitionRef.current || startingRef.current) return
    startingRef.current = true
    errorHandlerRef.current = onError
    const requestId = ++startRequestRef.current

    try {
      const permission = navigator.permissions?.query
        ? await navigator.permissions.query({ name: 'microphone' })
        : null
      if (permission?.state === 'denied') {
        if (requestId !== startRequestRef.current) return
        startingRef.current = false
        reportError(
          'Microphone access is blocked. Allow microphone access for this site in Chrome site settings, then try again.',
          'माइक्रोफ़ोन की अनुमति बंद है। Chrome की साइट सेटिंग में इस साइट के लिए माइक्रोफ़ोन की अनुमति दें, फिर दोबारा कोशिश करें।'
        )
        return
      }
    } catch {
      // Some browsers do not expose microphone permission queries; recognition can still request access.
    }

    if (requestId !== startRequestRef.current) return

    let recognition
    try {
      recognition = new SpeechRecognition()
    } catch {
      startingRef.current = false
      reportError(
        'Voice recognition could not start. Check your microphone and try again.',
        'वॉइस पहचान शुरू नहीं हो सकी। अपना माइक्रोफ़ोन जाँचकर फिर कोशिश करें।'
      )
      return
    }

    recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    let resultDelivered = false

    recognition.onstart = () => {
      if (recognitionRef.current === recognition) setIsListening(true)
    }
    recognition.onend = () => {
      if (recognitionRef.current === recognition) {
        startingRef.current = false
        setIsListening(false)
        recognitionRef.current = null
      }
    }

    recognition.onresult = (event) => {
      if (resultDelivered || recognitionRef.current !== recognition) return
      const transcript = event.results[event.resultIndex]?.[0]?.transcript
      if (transcript) {
        resultDelivered = true
        onResult(transcript)
      }
    }

    recognition.onerror = (event) => {
      if (recognitionRef.current !== recognition) return
      startingRef.current = false
      setIsListening(false)
      if (recognitionRef.current === recognition) recognitionRef.current = null
      if (event.error === 'aborted') return

      const errors = {
        'not-allowed': [
          'Microphone access was denied. Allow microphone access for this site in Chrome site settings, then try again.',
          'माइक्रोफ़ोन की अनुमति नहीं मिली। Chrome की साइट सेटिंग में इस साइट के लिए माइक्रोफ़ोन की अनुमति दें, फिर दोबारा कोशिश करें।',
        ],
        'service-not-allowed': [
          'Speech recognition is blocked by the browser. Check this site’s microphone permissions and try again.',
          'ब्राउज़र ने वॉइस पहचान को रोक दिया है। इस साइट की माइक्रोफ़ोन अनुमतियाँ जाँचें और फिर कोशिश करें।',
        ],
        'audio-capture': [
          'No microphone was found. Connect or enable a microphone, then try again.',
          'माइक्रोफ़ोन नहीं मिला। माइक्रोफ़ोन कनेक्ट या चालू करके फिर कोशिश करें।',
        ],
        'no-speech': [
          'No speech was detected. Please try speaking again.',
          'आपकी आवाज़ सुनाई नहीं दी। कृपया फिर से बोलें।',
        ],
        network: [
          'Speech recognition could not connect to the recognition service. Check your connection and try again.',
          'वॉइस पहचान सेवा से कनेक्ट नहीं हो सका। अपना इंटरनेट कनेक्शन जाँचकर फिर कोशिश करें।',
        ],
        'language-not-supported': [
          'Speech recognition does not support the selected language in this browser.',
          'इस ब्राउज़र में चुनी गई भाषा के लिए वॉइस पहचान उपलब्ध नहीं है।',
        ],
      }
      const message = errors[event.error]
      if (message) {
        reportError(message[0], message[1])
      } else {
        reportError(
          'Speech recognition stopped unexpectedly. Check your microphone and try again.',
          'वॉइस पहचान अचानक रुक गई। अपना माइक्रोफ़ोन जाँचकर फिर कोशिश करें।'
        )
      }
    }

    recognitionRef.current = recognition
    try {
      recognition.start()
      setIsListening(true)
    } catch {
      if (recognitionRef.current === recognition) {
        startingRef.current = false
        recognitionRef.current = null
        setIsListening(false)
      }
      reportError(
        'Voice recognition could not start. Check your microphone and try again.',
        'वॉइस पहचान शुरू नहीं हो सकी। अपना माइक्रोफ़ोन जाँचकर फिर कोशिश करें।'
      )
    }
  }, [lang, SpeechRecognition, supported])

  /**
   * Stop listening (if active).
   */
  const stopListening = useCallback(() => {
    startRequestRef.current += 1
    startingRef.current = false
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch {
        recognitionRef.current = null
        errorHandlerRef.current?.(
          lang === 'hi'
            ? 'वॉइस पहचान बंद नहीं हो सकी। कृपया फिर कोशिश करें।'
            : 'Voice recognition could not be stopped. Please try again.'
        )
      }
      setIsListening(false)
    }
  }, [lang])

  useEffect(() => () => {
    startRequestRef.current += 1
    startingRef.current = false
    if (recognitionRef.current) {
      recognitionRef.current.onstart = null
      recognitionRef.current.onend = null
      recognitionRef.current.onresult = null
      recognitionRef.current.onerror = null
      try {
        recognitionRef.current.abort()
      } catch {
        // The recognition may already have stopped.
      }
      recognitionRef.current = null
    }
  }, [])

  /**
   * Read text aloud using text-to-speech.
   * @param {string} text - The text to speak
   */
  const speak = useCallback((text) => {
    if (!window.speechSynthesis) return
    // Cancel any ongoing speech first
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    utterance.rate = 0.9    // Slightly slower for clarity
    utterance.pitch = 1.0
    window.speechSynthesis.speak(utterance)
  }, [lang])

  const cancelSpeech = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
  }, [])

  return { isListening, startListening, stopListening, speak, cancelSpeech, supported }
}
