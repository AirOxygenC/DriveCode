"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Mic,
  MicOff,
  ArrowLeft,
  FolderGit2,
  Bot,
  User,
  Loader2,
  CheckCircle2,
} from "lucide-react"

interface Repo {
  id: number
  name: string
  full_name: string
  private: boolean
  language: string | null
  updated_at: string
}

interface Message {
  role: "user" | "assistant"
  content: string
}

interface VoiceInterfaceProps {
  selectedRepo: Repo
  onBack: () => void
  token: string | null
}

export function VoiceInterface({ selectedRepo, onBack, token }: VoiceInterfaceProps) {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [status, setStatus] = useState<"connected" | "listening" | "processing" | "speaking">("connected")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const audioQueueRef = useRef<HTMLAudioElement[]>([])
  const isPlayingRef = useRef(false)

  const [socket, setSocket] = useState<any>(null)

  // Initialize Socket.IO connection
  useEffect(() => {
    // Dynamic import to avoid SSR issues if needed, but standard import is fine for client components
    const io = require("socket.io-client")
    const newSocket = io("http://localhost:5000", {
      transports: ["websocket"],
      auth: {
        token: token
      }
    })

    newSocket.on("connect", () => {
      console.log("Connected to Voice Loop Backend")
      setStatus("connected")
    })

    newSocket.on("status_change", (data: any) => {
      // Map backend states to frontend states
      // Backend: IDLE, ANALYZING, GENERATING, VERIFYING, AUDITING, MERGING
      console.log("Status change:", data)
      if (data.state === "ANALYZING" || data.state === "GENERATING") {
        setStatus("processing")
      } else if (data.state === "IDLE") {
        setStatus("connected")
      }

      // Add system message if description is provided
      if (data.description) {
        setMessages((prev) => [...prev, { role: "assistant", content: `[System]: ${data.description}` }])
      }
    })

    newSocket.on("user_message", (data: any) => {
      setMessages((prev) => [...prev, { role: "user", content: data.content }])
      setTranscript("")
    })

    newSocket.on("audio_response", (data: any) => {
      try {
        console.log("🔊 TTS audio received")
        const hexString = data.audio
        const bytes = new Uint8Array(hexString.match(/.{1,2}/g).map((byte: string) => parseInt(byte, 16)))
        const blob = new Blob([bytes], { type: 'audio/mpeg' })
        const audioUrl = URL.createObjectURL(blob)
        const audio = new Audio(audioUrl)

        // Add to queue
        audioQueueRef.current.push(audio)

        // Start playing if not already playing
        if (!isPlayingRef.current) {
          const playNextAudio = () => {
            if (audioQueueRef.current.length === 0) {
              isPlayingRef.current = false
              return
            }

            isPlayingRef.current = true
            const audio = audioQueueRef.current.shift()!

            audio.onended = () => {
              playNextAudio()
            }

            audio.onerror = (err) => {
              console.error("❌ Audio playback error:", err)
              playNextAudio()
            }

            audio.play()
              .then(() => console.log("✅ Playing TTS"))
              .catch(err => {
                console.error("❌ TTS play error:", err)
                playNextAudio()
              })
          }
          playNextAudio()
        }
      } catch (err) {
        console.error("❌ TTS processing error:", err)
      }
    })

    newSocket.on("audio_output", (data: any) => {
      // Handle audio stream (for now just log it, or we could play it)
      console.log("Received audio output", data)
      setStatus("speaking")
      // Reset to connected after a bit
      setTimeout(() => setStatus("connected"), 3000)
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0 && socket) {
          socket.emit("audio_stream", event.data)
        }
      }

      recorder.start(1000) // Chunk every 1 second
      setIsListening(true)
      setStatus("listening")
      setTranscript("Listening...")
    } catch (err) {
      console.error("Error accessing microphone:", err)
      setIsListening(false)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())

      if (socket) {
        // Send end of speech with repo context
        socket.emit("end_of_speech", {
          repo_name: selectedRepo.full_name
        })
      }

      setIsListening(false)
      setTranscript("Processing...")
    }
  }

  const toggleListening = () => {
    if (isListening) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const handleEndSession = () => {
    onBack()
  }

  const getStatusConfig = () => {
    switch (status) {
      case "listening":
        return { text: "Listening...", color: "bg-destructive/10 text-destructive border-destructive/20" }
      case "processing":
        return { text: "Processing...", color: "bg-accent/10 text-accent border-accent/20" }
      case "speaking":
        return { text: "Speaking...", color: "bg-accent/10 text-accent border-accent/20" }
      default:
        return { text: "Connected", color: "bg-success/10 text-success border-success/20" }
    }
  }

  const statusConfig = getStatusConfig()

  return (
    <main className="min-h-screen bg-background flex flex-col max-w-3xl mx-auto p-4 relative overflow-hidden">
      {/* Ambient background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-success/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 flex flex-col h-[calc(100vh-2rem)] gap-4">
        {/* Header */}
        <Card className="bg-card/50 backdrop-blur-xl border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>

              <Badge variant="secondary" className="bg-accent/10 text-accent border-accent/20 px-4 py-1.5">
                <FolderGit2 className="h-3.5 w-3.5 mr-2" />
                {selectedRepo.name}
              </Badge>

              <Badge variant="secondary" className={`${statusConfig.color} px-3 py-1.5`}>
                {status === "listening" && (
                  <span className="relative flex h-2 w-2 mr-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-destructive" />
                  </span>
                )}
                {status === "connected" && <CheckCircle2 className="h-3.5 w-3.5 mr-2" />}
                {(status === "processing" || status === "speaking") && (
                  <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                )}
                {statusConfig.text}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Messages Area */}
        <Card className="flex-1 bg-card/50 backdrop-blur-xl border-border/50 overflow-hidden">
          <ScrollArea className="h-full">
            <CardContent className="p-6">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-[40vh] text-center space-y-4">
                  <div className="p-6 rounded-2xl bg-secondary/30 border border-border/50">
                    <Mic className="h-12 w-12 text-muted-foreground" />
                  </div>
                  <div className="space-y-2">
                    <h2 className="text-xl font-semibold text-foreground">Ready for Voice Commands</h2>
                    <p className="text-muted-foreground max-w-sm">
                      Press the microphone button and tell me what you want to build. I'll turn your ideas into code.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300 ${msg.role === "user" ? "flex-row-reverse" : ""
                        }`}
                    >
                      <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${msg.role === "user"
                        ? "bg-accent/20"
                        : "bg-secondary"
                        }`}>
                        {msg.role === "user" ? (
                          <User className="h-5 w-5 text-accent" />
                        ) : (
                          <Bot className="h-5 w-5 text-muted-foreground" />
                        )}
                      </div>
                      <div className={`max-w-[75%] p-4 rounded-2xl ${msg.role === "user"
                        ? "bg-accent text-accent-foreground rounded-br-md"
                        : "bg-secondary text-foreground rounded-bl-md"
                        }`}>
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </CardContent>
          </ScrollArea>
        </Card>

        {/* Transcript Bar */}
        {transcript && (
          <Card className="bg-accent/10 border-accent/30 animate-in fade-in slide-in-from-bottom-2 duration-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-destructive" />
                </span>
                <p className="text-foreground">{transcript}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Voice Controls */}
        <Card className="bg-card/50 backdrop-blur-xl border-border/50">
          <CardContent className="p-6">
            <div className="flex items-center justify-center gap-6">
              <button
                onClick={toggleListening}
                disabled={isProcessing}
                className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${isListening
                  ? "bg-destructive hover:bg-destructive/90 shadow-lg shadow-destructive/40"
                  : isProcessing
                    ? "bg-muted cursor-not-allowed"
                    : "bg-accent hover:bg-accent/90 hover:scale-105 shadow-lg shadow-accent/40"
                  } ${isListening ? "animate-pulse" : ""}`}
                aria-label={isListening ? "Stop listening" : "Start listening"}
              >
                {isProcessing ? (
                  <Loader2 className="h-8 w-8 text-muted-foreground animate-spin" />
                ) : isListening ? (
                  <MicOff className="h-8 w-8 text-destructive-foreground" />
                ) : (
                  <Mic className="h-8 w-8 text-accent-foreground" />
                )}

                {/* Pulse ring animation when listening */}
                {isListening && (
                  <>
                    <span className="absolute inset-0 rounded-full bg-destructive/50 animate-ping" />
                    <span className="absolute inset-[-8px] rounded-full border-2 border-destructive/30 animate-pulse" />
                  </>
                )}
              </button>

              <Button
                variant="outline"
                size="lg"
                onClick={handleEndSession}
                className="h-14 px-8 text-base font-semibold border-2 border-success text-success hover:bg-success hover:text-success-foreground transition-all duration-200 bg-transparent"
              >
                {"I'm Done"}
              </Button>
            </div>

            <p className="text-center text-xs text-muted-foreground mt-4">
              {isListening
                ? "Speak your idea clearly. I'm listening..."
                : isProcessing
                  ? "Processing your request..."
                  : "Tap the microphone to start speaking"}
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
